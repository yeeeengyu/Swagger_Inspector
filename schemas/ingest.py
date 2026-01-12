from pydantic import BaseModel, Field
from typing import Dict

class IngestRequest(BaseModel):
    url: str = Field(..., description="OpenAPI 스펙 URL 또는 Swagger UI URL")
    headers: Dict[str, str] = Field(default_factory=dict)
    include_operations: bool = True
    include_schemas: bool = True
    max_text_chars: int = 2000

class IngestResponse(BaseModel):
    resolved_spec_url: str
    docs: int
    dim: int
