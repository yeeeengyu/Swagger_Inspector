from __future__ import annotations
import json
from typing import Any, Dict, List, Tuple

from openai import OpenAI
from fastapi import HTTPException

from core.config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, FALLBACK_MESSAGE

def build_context(results: List[Tuple[Dict[str, Any], float]], max_chars: int = 8000) -> str:
    blocks: List[str] = []
    total = 0
    for doc, score in results:
        block = (
            f"[DOC_ID] {doc.get('doc_id')}\n"
            f"[SCORE] {score:.4f}\n"
            f"[TITLE] {doc.get('title')}\n"
            f"[META] {json.dumps(doc.get('metadata', {}), ensure_ascii=False)}\n\n"
            f"{doc.get('text','')}"
        )
        if total + len(block) > max_chars:
            break
        blocks.append(block)
        total += len(block)
    return "\n\n---\n\n".join(blocks)

def make_fallback(results: List[Tuple[Dict[str, Any], float]]) -> Tuple[str, List[Dict[str, Any]]]:
    cits: List[Dict[str, Any]] = []
    for doc, score in results[:3]:
        meta = doc.get("metadata", {}) or {}
        cits.append(
            {
                "doc_id": doc.get("doc_id"),
                "title": doc.get("title"),
                "score": score,
                "method": meta.get("method"),
                "path": meta.get("path"),
            }
        )

    if cits:
        hint = "유사 후보:\n" + "\n".join(
            [f"- {c.get('method','')} {c.get('path','')} ({c['score']:.2f}) {c['title']}" for c in cits]
        )
        return f"{FALLBACK_MESSAGE}\n\n{hint}", cits

    return FALLBACK_MESSAGE, []

def call_chat(query: str, context: str) -> str:
    if not OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY가 없습니다.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    system = (
        "너는 API 문서(스웨거) 기반 도우미다.\n"
        "반드시 CONTEXT 안에서만 답하고, 없으면 '문서 근거 없음'이라고 말해라.\n"
        "추측 금지. 답변에 관련 endpoint를 method+path로 명시해라.\n"
    )

    user = (
        f"QUERY:\n{query}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "요구사항:\n"
        "- 가능하면 curl 예시 1개\n"
        "- 필요한 파라미터/바디 필드가 있으면 표로 정리\n"
    )

    resp = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()
