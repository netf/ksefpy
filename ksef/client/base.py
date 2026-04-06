from __future__ import annotations

import logging
from typing import Any

import httpx

from ksef.environments import Environment
from ksef.exceptions import _ApiError

logger = logging.getLogger("ksef")


class BaseClient:
    """Low-level HTTP wrapper for the KSeF API."""

    def __init__(
        self,
        environment: Environment,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.environment = environment
        self._base_url = environment.api_base_url.rstrip("/")
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def __aenter__(self) -> BaseClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _headers(self, access_token: str | None = None) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def _handle_response(self, response: httpx.Response) -> Any:
        status = response.status_code
        logger.debug("HTTP %s %s -> %d", response.request.method, response.request.url, status)

        if status == 204:
            return None

        if 200 <= status < 300:
            if not response.content or response.content.isspace():
                return None
            return response.json()

        body: dict[str, Any] = {}
        try:
            body = response.json()
        except Exception:
            pass

        retry_after: float | None = None
        if status == 429:
            raw = response.headers.get("Retry-After")
            if raw:
                try:
                    retry_after = float(raw)
                except ValueError:
                    pass

        message = body.get("title", "") or f"API error {status}"
        if not body and response.text:
            message = f"API error {status}: {response.text[:200]}"

        raise _ApiError(
            message,
            status_code=status,
            raw_response=body,
            retry_after=retry_after,
        )

    async def get(
        self,
        path: str,
        *,
        access_token: str | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        h = self._headers(access_token)
        if headers:
            h.update(headers)
        response = await self._http.get(self._url(path), headers=h, params=params)
        return await self._handle_response(response)

    async def post(
        self,
        path: str,
        *,
        access_token: str | None = None,
        json: Any = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        h = self._headers(access_token)
        if headers:
            h.update(headers)
        response = await self._http.post(self._url(path), headers=h, json=json, content=content, params=params)
        return await self._handle_response(response)

    async def put(
        self,
        path: str,
        *,
        access_token: str | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        h = self._headers(access_token)
        if headers:
            h.update(headers)
        response = await self._http.put(self._url(path), headers=h, content=content)
        return await self._handle_response(response)

    async def get_raw(
        self, path: str, *, access_token: str | None = None, headers: dict[str, str] | None = None
    ) -> bytes:
        """GET that returns raw response bytes instead of parsed JSON."""
        h = self._headers(access_token)
        h["Accept"] = "*/*"  # raw endpoints may return XML, not JSON
        if headers:
            h.update(headers)
        response = await self._http.get(self._url(path), headers=h)
        if response.status_code >= 400:
            await self._handle_response(response)
        return response.content

    async def put_raw(
        self, url: str, *, content: bytes | None = None, headers: dict[str, str] | None = None
    ) -> None:
        """PUT to an absolute URL (for batch part uploads). No base URL prefix.

        The URL must use HTTPS to prevent SSRF attacks.
        """
        if not url.startswith("https://"):
            raise ValueError(f"put_raw requires HTTPS URL, got: {url[:50]}")
        response = await self._http.put(url, content=content, headers=headers or {})
        if response.status_code >= 400:
            await self._handle_response(response)

    async def delete(self, path: str, *, access_token: str | None = None) -> Any:
        response = await self._http.delete(self._url(path), headers=self._headers(access_token))
        return await self._handle_response(response)
