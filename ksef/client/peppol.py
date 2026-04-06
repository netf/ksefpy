from __future__ import annotations
from typing import Any
from ksef.client.base import BaseClient


class PeppolClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def query(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("peppol/query", access_token=access_token, json=request)
