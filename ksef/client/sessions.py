from __future__ import annotations
from typing import Any
from ksef.client.base import BaseClient


class ActiveSessionsClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def list_sessions(self, *, access_token: str, params: dict[str, Any] | None = None) -> dict:
        return await self._base.get("auth/sessions", access_token=access_token, params=params)

    async def invalidate_current(self, *, access_token: str) -> None:
        await self._base.delete("auth/sessions/current", access_token=access_token)

    async def invalidate(self, reference_number: str, *, access_token: str) -> None:
        await self._base.delete(f"auth/sessions/{reference_number}", access_token=access_token)
