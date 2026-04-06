from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class BatchSessionClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def open(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("sessions/batch", access_token=access_token, json=request)

    async def upload_part(self, url: str, encrypted_part: bytes, *, headers: dict[str, str] | None = None) -> None:
        await self._base.put_raw(url, content=encrypted_part, headers=headers)

    async def close(self, session_reference_number: str, *, access_token: str) -> None:
        await self._base.post(f"sessions/batch/{session_reference_number}/close", access_token=access_token)
