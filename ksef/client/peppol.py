from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class PeppolClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def query(self, *, access_token: str, params: dict[str, Any] | None = None) -> dict:
        """GET /peppol/query"""
        return await self._base.get("peppol/query", access_token=access_token, params=params)
