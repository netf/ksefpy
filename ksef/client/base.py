from __future__ import annotations

import logging
from typing import Any

import httpx

from ksef.environments import Environment
from ksef.exceptions import (
    KSeFApiError,
    KSeFForbiddenError,
    KSeFRateLimitError,
    KSeFServerError,
    KSeFUnauthorizedError,
)

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

        if status == 401:
            raise KSeFUnauthorizedError(
                message=body.get("title", "Unauthorized"),
                problem=body,
            )
        if status == 403:
            raise KSeFForbiddenError(
                message=body.get("title", "Forbidden"),
                problem=body,
            )
        if status == 429:
            retry_after: float | None = None
            raw = response.headers.get("Retry-After")
            if raw:
                try:
                    retry_after = float(raw)
                except ValueError:
                    pass
            raise KSeFRateLimitError(
                message="Rate limited",
                retry_after=retry_after,
            )
        if status >= 500:
            raise KSeFServerError(
                message=body.get("title", response.text[:200] if response.text else "Server error"),
                status_code=status,
            )

        error_code: str | None = None
        details: list[dict[str, Any]] = []
        if "exception" in body:
            exc_content = body["exception"]
            error_code = exc_content.get("serviceCode")
            details = exc_content.get("exceptionDetailList", [])

        message = f"API error {status}"
        if not error_code and not details and response.text:
            message = f"API error {status}: {response.text[:200]}"
        raise KSeFApiError(
            message=message,
            status_code=status,
            error_code=error_code,
            details=details,
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
        """PUT to an absolute URL (for batch part uploads). No base URL prefix."""
        response = await self._http.put(url, content=content, headers=headers or {})
        if response.status_code >= 400:
            await self._handle_response(response)

    async def delete(self, path: str, *, access_token: str | None = None) -> Any:
        response = await self._http.delete(self._url(path), headers=self._headers(access_token))
        return await self._handle_response(response)
