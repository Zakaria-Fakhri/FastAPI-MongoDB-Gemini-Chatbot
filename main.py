import asyncio
import json
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import TypeAdapter

from db import init_db, get_db, close_db
from models import ArticleIn, UploadResult, ChatRequest, ChatResponse
from utils import build_context_from_articles
from gemini_client import chat_complete
import os

app = FastAPI(title="FastAPI MongoDB Gemini Chatbot")


@app.on_event("shutdown")
async def on_shutdown():
    await close_db()


@app.post("/upload", response_model=UploadResult)
async def upload_json(file: UploadFile = File(...)):
    """Accepts a JSON file of articles and stores them in MongoDB."""
    # Lazy DB init to allow server startup without a running MongoDB
    try:
        await init_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB init error: {e}")
    if not file.filename.lower().endswith((".json",)):
        raise HTTPException(status_code=400, detail="Please upload a JSON file.")

    raw = await file.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")

    adapter = TypeAdapter(List[ArticleIn])
    try:
        articles: List[ArticleIn] = adapter.validate_python(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")

    db = get_db()
    coll = db["articles"]

    # Upsert by title to avoid duplicates
    from pymongo import UpdateOne

    ops = []
    for art in articles:
        doc = art.model_dump()
        ops.append(
            UpdateOne({"title": doc["title"]}, {"$set": doc}, upsert=True)
        )

    if not ops:
        return UploadResult(upserted=0, modified=0, matched=0)

    try:
        result = await coll.bulk_write(ops)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB write error: {e}")

    # result.upserted_count, result.modified_count, result.matched_count
    return UploadResult(
        upserted=result.upserted_count,
        modified=result.modified_count,
        matched=result.matched_count,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Answers a question strictly based on the stored articles."""
    # Lazy DB init; if DB not reachable, return safe fallback
    try:
        await init_db()
        db = get_db()
        coll = db["articles"]
    except Exception:
        return ChatResponse(answer="I don't have information on that.")
    try:
        articles = await coll.find({}, {"_id": 0, "title": 1, "content": 1}).to_list(length=10000)
    except Exception:
        return ChatResponse(answer="I don't have information on that.")

    if not articles:
        return ChatResponse(answer="I don't have information on that.")

    context = build_context_from_articles(articles)

    # Offload Gemini call to a thread to avoid blocking the event loop
    try:
        answer = await asyncio.to_thread(chat_complete, context, req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}")

    # Post-guard: if model didn't follow instruction, do a simple guard
    if not answer or answer.strip() == "" or "I don't have information" in answer:
        return ChatResponse(answer="I don't have information on that.")

    # Heuristic: if the answer includes phrases indicating it's out of context, then fallback
    lowered = answer.lower()
    if any(kw in lowered for kw in ["no information", "not in context", "out of context"]):
        return ChatResponse(answer="I don't have information on that.")

    return ChatResponse(answer=answer)


@app.get("/")
async def root():
    """Health check."""
    return JSONResponse({"status": "ok"})
