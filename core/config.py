import os
from dotenv import load_dotenv

load_dotenv()

# Mongo
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "")
MONGODB_COL = os.getenv("MONGODB_COL", "")
VECTOR_INDEX = os.getenv("VECTOR_INDEX", "")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
DEFAULT_THRESHOLD = float(os.getenv("DEFAULT_THRESHOLD", "0.80"))

FALLBACK_MESSAGE = os.getenv(
    "FALLBACK_MESSAGE",
    "문서 근거를 찾지 못했습니다. 기능 키워드 또는 엔드포인트 경로를 포함해 다시 질문해주세요.",
)
