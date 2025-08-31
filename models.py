from typing import List
from pydantic import BaseModel, Field


class ArticleIn(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class UploadResult(BaseModel):
    upserted: int
    modified: int
    matched: int


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
