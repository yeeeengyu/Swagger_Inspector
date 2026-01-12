from pydantic import BaseModel
from typing import Any, Dict, List
import os

DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
DEFAULT_THRESHOLD = float(os.getenv("DEFAULT_THRESHOLD", "0.80"))

class ChatRequest(BaseModel):
    query: str
    top_k: int = DEFAULT_TOP_K
        

class ChatResponse(BaseModel):
    query: str
    used_llm: bool
    threshold: float
    top_score: float
    answer: str
    citations: List[Dict[str, Any]]
