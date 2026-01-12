from __future__ import annotations
import re
from typing import Any, Dict
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import HTTPException

async def fetch_json(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as c:
        r = await c.get(url, headers=headers)
        r.raise_for_status()
        return r.json()

async def _fetch_text(url: str, headers: Dict[str, str]) -> str:
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as c:
        r = await c.get(url, headers=headers)
        r.raise_for_status()
        return r.text

def _origin(url: str) -> str:
    u = urlparse(url)
    return f"{u.scheme}://{u.netloc}"

async def resolve_spec_url(url: str, headers: Dict[str, str]) -> str:
    u = url.lower()

    # 이미 스펙 URL이면 그대로
    if u.endswith(".json") or u.endswith(".yaml") or "openapi" in u or "api-docs" in u:
        return url

    base = _origin(url)
    candidates = [
        urljoin(base + "/", "openapi.json"),
        urljoin(base + "/", "v3/api-docs"),
        urljoin(base + "/", "v3/api-docs/swagger-config"),
    ]

    # 흔한 후보들 먼저
    for c in candidates:
        try:
            data = await fetch_json(c, headers)
            if "openapi" in data or "paths" in data:
                return c
            # swagger-config 형태
            if "url" in data and isinstance(data["url"], str):
                return urljoin(base + "/", data["url"].lstrip("/"))
            if "urls" in data and isinstance(data["urls"], list) and data["urls"]:
                first = data["urls"][0]
                if isinstance(first, dict) and "url" in first:
                    return urljoin(base + "/", str(first["url"]).lstrip("/"))
        except Exception:
            pass

    # Swagger UI HTML에서 spec url 추출
    try:
        html = await _fetch_text(url, headers)
        m = re.search(r'url\s*:\s*"([^"]+)"', html)
        if m:
            return urljoin(base + "/", m.group(1).lstrip("/"))

        m2 = re.search(r'configUrl\s*:\s*"([^"]+)"', html)
        if m2:
            cfg = urljoin(base + "/", m2.group(1).lstrip("/"))
            data = await fetch_json(cfg, headers)
            if "url" in data:
                return urljoin(base + "/", str(data["url"]).lstrip("/"))
            if "urls" in data and data["urls"]:
                first = data["urls"][0]
                if isinstance(first, dict) and "url" in first:
                    return urljoin(base + "/", str(first["url"]).lstrip("/"))
    except Exception:
        pass

    raise HTTPException(
        400,
        "OpenAPI 스펙 URL을 자동으로 찾지 못했습니다. /openapi.json 또는 /v3/api-docs 같은 스펙 URL을 직접 넣으세요.",
    )
