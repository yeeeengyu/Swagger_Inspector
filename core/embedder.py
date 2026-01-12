from __future__ import annotations
from typing import List
import numpy as np
from fastapi import HTTPException
from openai import OpenAI

from core.config import OPENAI_API_KEY, OPENAI_EMBED_MODEL

def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    eps = 1e-12
    n = np.linalg.norm(mat, axis=1, keepdims=True)
    return mat / np.maximum(n, eps)

class Embedder:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise HTTPException(500, "OPENAI_API_KEY가 없습니다.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def embed(self, texts: List[str]) -> np.ndarray:
        resp = self.client.embeddings.create(model=OPENAI_EMBED_MODEL, input=texts)
        vecs = np.array([d.embedding for d in resp.data], dtype=np.float32)
        return _l2_normalize(vecs)
