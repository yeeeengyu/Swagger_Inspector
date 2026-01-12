from __future__ import annotations
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas.ingest import IngestRequest, IngestResponse
from schemas.chat import ChatRequest, ChatResponse
from schemas.doc import Doc

from core.config import DEFAULT_TOP_K, DEFAULT_THRESHOLD
from core.embedder import Embedder
from core.openapi_fetch import resolve_spec_url, fetch_json
from core.openapi_parse import make_docs_from_openapi
from core.llm import build_context, call_chat, make_fallback

from db.mongo_store import MongoVectorStore

app = FastAPI(title="Swagger Threshold Chatbot (Mongo Atlas Vector Search)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = MongoVectorStore()
embedder = Embedder()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "docs": store.count(),
        "default_top_k": DEFAULT_TOP_K,
        "default_threshold": DEFAULT_THRESHOLD,
    }


@app.post("/reset")
def reset() -> Dict[str, Any]:
    deleted = store.reset()
    return {"status": "reset_ok", "deleted": deleted}


@app.post("/ingest/openapi", response_model=IngestResponse)
async def ingest_openapi(req: IngestRequest) -> IngestResponse:
    spec_url = await resolve_spec_url(req.url, req.headers)
    spec = await fetch_json(spec_url, req.headers)

    docs: List[Doc] = make_docs_from_openapi(
        spec=spec,
        include_operations=req.include_operations,
        include_schemas=req.include_schemas,
        max_text_chars=req.max_text_chars,
    )
    if not docs:
        raise HTTPException(400, "문서화할 operation/schema가 없습니다.")

    vecs = embedder.embed([d.text for d in docs])

    # upsert용 dict로 변환
    rows = [
        {
            "doc_id": d.doc_id,
            "kind": d.kind,
            "title": d.title,
            "text": d.text,
            "metadata": d.metadata,
        }
        for d in docs
    ]
    store.reset()
    store.upsert_docs(rows, vecs)

    return IngestResponse(resolved_spec_url=spec_url, docs=len(docs), dim=int(vecs.shape[1]))


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if store.count() == 0:
        raise HTTPException(400, "먼저 /ingest/openapi 로 스펙을 인덱싱하세요.")

    qv = embedder.embed([req.query])
    results: List[Tuple[Dict[str, Any], float]] = store.search(qv, req.top_k)

    top_score = results[0][1] if results else 0.0

    # 내부 threshold 기준으로 자동 게이트
    should_call_llm = top_score >= DEFAULT_THRESHOLD

    if not should_call_llm:
        answer, cits = make_fallback(results)
        return ChatResponse(
            query=req.query,
            used_llm=False,
            threshold=DEFAULT_THRESHOLD,
            top_score=top_score,
            answer=answer,
            citations=cits,
        )

    context = build_context(results)
    answer = call_chat(req.query, context)

    cits = []
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

    return ChatResponse(
        query=req.query,
        used_llm=True,
        threshold=DEFAULT_THRESHOLD,
        top_score=top_score,
        answer=answer,
        citations=cits,
    )
