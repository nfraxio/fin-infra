from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_DEFAULT_TIMEOUT = httpx.Timeout(20.0)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True,
)
async def aget_json(url: str, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        r = await client.get(url, **kwargs)
        r.raise_for_status()
        return r.json()
