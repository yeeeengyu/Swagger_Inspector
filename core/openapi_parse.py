from __future__ import annotations
import re
from typing import Any, Dict, List

from schemas.doc import Doc

_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}

def _truncate(s: str, max_chars: int) -> str:
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s[:max_chars]

def _indent(s: str, n: int) -> str:
    pad = " " * n
    return "\n".join(pad + line for line in s.splitlines())

def _summarize_schema(schema: Dict[str, Any], depth: int = 0, max_depth: int = 2) -> str:
    if not isinstance(schema, dict):
        return ""

    if "$ref" in schema:
        return f"ref: {schema['$ref']}"

    t = schema.get("type")
    desc = schema.get("description", "") or ""

    lines: List[str] = []
    if t: lines.append(f"type: {t}")
    if desc: lines.append(f"desc: {desc}")

    if depth >= max_depth:
        return " | ".join(lines).strip()

    if t == "object":
        props = schema.get("properties", {}) or {}
        req = set(schema.get("required", []) or [])
        if props:
            lines.append("fields:")
            for k, v in list(props.items())[:40]:
                vt = v.get("type") or ("ref" if "$ref" in v else "")
                vd = v.get("description", "") or ""
                star = " (required)" if k in req else ""
                lines.append(f"- {k}: {vt}{star} {vd}".strip())

    if t == "array":
        items = schema.get("items", {}) or {}
        lines.append(f"items: {_summarize_schema(items, depth+1, max_depth)}")

    return "\n".join(lines).strip()

def make_docs_from_openapi(
    spec: Dict[str, Any],
    include_operations: bool,
    include_schemas: bool,
    max_text_chars: int,
) -> List[Doc]:
    docs: List[Doc] = []

    if include_operations:
        paths = spec.get("paths", {}) or {}
        for path, item in paths.items():
            if not isinstance(item, dict):
                continue
            for method, op in item.items():
                if method.lower() not in _HTTP_METHODS:
                    continue
                if not isinstance(op, dict):
                    continue

                m = method.upper()
                summary = op.get("summary", "") or ""
                desc = op.get("description", "") or ""
                tags = op.get("tags", []) or []
                operation_id = op.get("operationId", "") or ""

                # parameters
                params = op.get("parameters", []) or []
                p_lines: List[str] = []
                for p in params[:60]:
                    if not isinstance(p, dict):
                        continue
                    name = p.get("name", "")
                    where = p.get("in", "")
                    required = bool(p.get("required", False))
                    pdesc = p.get("description", "") or ""
                    schema = p.get("schema", {}) or {}
                    ptype = schema.get("type", "") or ("ref" if "$ref" in schema else "")
                    p_lines.append(f"- {name} ({where}) type={ptype} required={required} {pdesc}".strip())

                # requestBody
                rb = op.get("requestBody", {}) or {}
                rb_desc = rb.get("description", "") or ""
                rb_content = rb.get("content", {}) or {}
                rb_schema_txt = ""
                if isinstance(rb_content, dict) and rb_content:
                    ct = "application/json" if "application/json" in rb_content else next(iter(rb_content.keys()))
                    if isinstance(rb_content.get(ct), dict):
                        rb_schema = (rb_content[ct].get("schema", {}) or {})
                        rb_schema_txt = _summarize_schema(rb_schema)

                # responses
                resp = op.get("responses", {}) or {}
                r_lines: List[str] = []
                if isinstance(resp, dict):
                    for code, rv in list(resp.items())[:30]:
                        if not isinstance(rv, dict):
                            continue
                        rdesc = rv.get("description", "") or ""
                        rcontent = rv.get("content", {}) or {}
                        rschema_txt = ""
                        if isinstance(rcontent, dict) and rcontent:
                            ct = "application/json" if "application/json" in rcontent else next(iter(rcontent.keys()))
                            if isinstance(rcontent.get(ct), dict):
                                rschema = (rcontent[ct].get("schema", {}) or {})
                                rschema_txt = _summarize_schema(rschema)

                        block = f"- {code}: {rdesc}".strip()
                        if rschema_txt:
                            block += f"\n  schema:\n{_indent(rschema_txt, 4)}"
                        r_lines.append(block)

                title = f"{m} {path}"
                parts = [
                    f"[ENDPOINT] {m} {path}",
                    f"summary: {summary}" if summary else "",
                    f"description:\n{desc}" if desc else "",
                    f"tags: {', '.join(tags)}" if tags else "",
                    f"operationId: {operation_id}" if operation_id else "",
                    "parameters:\n" + "\n".join(p_lines) if p_lines else "",
                    "requestBody:\n" + (rb_desc + "\n" if rb_desc else "") + rb_schema_txt if (rb_desc or rb_schema_txt) else "",
                    "responses:\n" + "\n".join(r_lines) if r_lines else "",
                ]
                text = _truncate("\n\n".join([x for x in parts if x]).strip(), max_text_chars)

                doc_id = f"op::{m}::{path}::{operation_id or 'noid'}"
                docs.append(
                    Doc(
                        doc_id=doc_id,
                        kind="operation",
                        title=title,
                        text=text,
                        metadata={"method": m, "path": path, "tags": tags, "operationId": operation_id},
                    )
                )

    if include_schemas:
        schemas = ((spec.get("components", {}) or {}).get("schemas", {}) or {})
        if isinstance(schemas, dict):
            for name, schema in schemas.items():
                if not isinstance(schema, dict):
                    continue
                body = _summarize_schema(schema)
                text = _truncate(f"[SCHEMA] {name}\n\n{body}".strip(), max_text_chars)
                docs.append(
                    Doc(
                        doc_id=f"schema::{name}",
                        kind="schema",
                        title=f"SCHEMA {name}",
                        text=text,
                        metadata={"schema": name},
                    )
                )

    return docs
