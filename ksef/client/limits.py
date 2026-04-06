from __future__ import annotations

from ksef.client.base import BaseClient


class LimitsClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def get_context_limits(self, *, access_token: str) -> dict:
        return await self._base.get("limits/context", access_token=access_token)

    async def get_subject_limits(self, *, access_token: str) -> dict:
        return await self._base.get("limits/subject", access_token=access_token)

    async def get_rate_limits(self, *, access_token: str) -> dict:
        return await self._base.get("rate-limits", access_token=access_token)
