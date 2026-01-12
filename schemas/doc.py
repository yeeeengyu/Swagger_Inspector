from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Doc:
    doc_id: str
    kind: str      # "operation" | "schema"
    title: str
    text: str
    metadata: Dict[str, Any]
