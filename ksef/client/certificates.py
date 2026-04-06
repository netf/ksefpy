from __future__ import annotations
from typing import Any
from ksef.client.base import BaseClient


class CertificateClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def get_limits(self, *, access_token: str) -> dict:
        return await self._base.get("certificates/limits", access_token=access_token)

    async def get_enrollment_data(self, *, access_token: str) -> dict:
        return await self._base.get("certificates/enrollments/data", access_token=access_token)

    async def enroll(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("certificates/enrollments", access_token=access_token, json=request)

    async def get_enrollment_status(self, reference_number: str, *, access_token: str) -> dict:
        return await self._base.get(f"certificates/enrollments/{reference_number}", access_token=access_token)

    async def retrieve(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("certificates/retrieve", access_token=access_token, json=request)

    async def revoke(self, serial_number: str, *, access_token: str) -> None:
        await self._base.post(f"certificates/{serial_number}/revoke", access_token=access_token)

    async def query(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("certificates/query", access_token=access_token, json=request)
