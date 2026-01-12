from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
from fastapi import HTTPException
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError

from core.config import MONGODB_URI, MONGODB_DB, MONGODB_COL, VECTOR_INDEX

def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class MongoVectorStore:
    def __init__(self) -> None:
        self._client: Optional[MongoClient] = None

    def _col(self):
        if not (MONGODB_URI and MONGODB_DB and MONGODB_COL):
            raise HTTPException(500, "Mongo 환경변수(MONGODB_URI/DB/COL)가 설정되지 않았습니다.")
        if self._client is None:
            self._client = MongoClient(MONGODB_URI)
        return self._client[MONGODB_DB][MONGODB_COL]

    def reset(self) -> int:
        res = self._col().delete_many({})
        return int(res.deleted_count)

    def count(self) -> int:
        return int(self._col().count_documents({}))

    def upsert_docs(self, docs: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        ops: List[UpdateOne] = []
        for d, emb in zip(docs, embeddings):
            ops.append(
                UpdateOne(
                    {"doc_id": d["doc_id"]},
                    {
                        "$set": {
                            **d,
                            "embedding": emb.astype(float).tolist(),
                            "updated_at": _utc_iso(),
                        },
                        "$setOnInsert": {"created_at": _utc_iso()},
                    },
                    upsert=True,
                )
            )
        if ops:
            self._col().bulk_write(ops, ordered=False)

    def search(self, query_vec: np.ndarray, k: int) -> List[Tuple[Dict[str, Any], float]]:
        if not VECTOR_INDEX:
            raise HTTPException(500, "VECTOR_INDEX 환경변수가 설정되지 않았습니다.")

        k = max(1, k)
        pipeline = [
            {
                "$vectorSearch": {
                    "index": VECTOR_INDEX,
                    "path": "embedding",
                    "queryVector": query_vec[0].astype(float).tolist(),
                    "numCandidates": max(100, k * 20),
                    "limit": k,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "doc_id": 1,
                    "kind": 1,
                    "title": 1,
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        try:
            rows = list(self._col().aggregate(pipeline))
        except PyMongoError as e:
            raise HTTPException(
                500,
                "MongoDB $vectorSearch 실패. Atlas Search Index 존재/차원(numDimensions) 일치 확인 필요. "
                f"(error={str(e)[:180]})",
            )

        return [(r, float(r.get("score", 0.0))) for r in rows]
