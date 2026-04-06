from __future__ import annotations
from typing import Any
from ksef.client.base import BaseClient


class KSeFTokenClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def generate(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("tokens", access_token=access_token, json=request)

    async def list_tokens(self, *, access_token: str, params: dict[str, Any] | None = None) -> dict:
        return await self._base.get("tokens", access_token=access_token, params=params)

    async def get(self, reference_number: str, *, access_token: str) -> dict:
        return await self._base.get(f"tokens/{reference_number}", access_token=access_token)

    async def revoke(self, reference_number: str, *, access_token: str) -> None:
        await self._base.delete(f"tokens/{reference_number}", access_token=access_token)
