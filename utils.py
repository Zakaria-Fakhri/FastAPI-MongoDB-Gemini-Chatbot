from typing import List, Dict


def build_context_from_articles(articles: List[Dict], max_chars: int = 12000) -> str:
    parts: List[str] = []
    for art in articles:
        title = str(art.get("title", "")).strip()
        content = str(art.get("content", "")).strip()
        if not title and not content:
            continue
        parts.append(f"Title: {title}\nContent: {content}\n---")

    full = "\n".join(parts)
    if len(full) > max_chars:
        # Simple trim to fit
        full = full[:max_chars]
    return full
