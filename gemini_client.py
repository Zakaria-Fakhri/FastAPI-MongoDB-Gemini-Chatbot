"""Gemini client: generates answers based on a provided context.

Answers must strictly be based on the supplied context.
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
except Exception:
    genai = None  # Checked at runtime


def get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def chat_complete(context: str, question: str) -> str:
    """Produce an answer to a question within the given context."""
    if genai is None:
        raise RuntimeError("google-generativeai package is not installed")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    genai.configure(api_key=api_key)

    system = (
        "You are a helpful assistant. Answer ONLY based on the provided context. "
        "If the question cannot be answered from the context, answer exactly: 'I don't have information on that.'"
    )

    prompt = (
        f"{system}\n\nContext (articles):\n{context}\n\n"
        f"Question: {question}\n"
    )

    model_name = get_model_name()
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(prompt)
    text = getattr(resp, "text", None) or ""
    text = text.strip()
    if not text:
        return "I don't have information on that."
    # Guard-rail heuristic
    lowered = text.lower()
    if any(kw in lowered for kw in ["no information", "not in context", "out of context"]):
        return "I don't have information on that."
    return text
