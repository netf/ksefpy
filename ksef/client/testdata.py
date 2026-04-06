from __future__ import annotations
from typing import Any
from ksef.client.base import BaseClient


class TestDataClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def create_subject(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/subject", access_token=access_token, json=request)

    async def remove_subject(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/subject/remove", access_token=access_token, json=request)

    async def create_person(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/person", access_token=access_token, json=request)

    async def remove_person(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/person/remove", access_token=access_token, json=request)

    async def grant_permissions(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/permissions", access_token=access_token, json=request)

    async def revoke_permissions(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/permissions/revoke", access_token=access_token, json=request)

    async def enable_attachments(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/attachment", access_token=access_token, json=request)

    async def disable_attachments(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/attachment/revoke", access_token=access_token, json=request)

    async def change_session_limits(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/limits/context/session", access_token=access_token, json=request)

    async def reset_session_limits(self, *, access_token: str) -> None:
        await self._base.delete("testdata/limits/context/session", access_token=access_token)

    async def change_certificate_limits(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/limits/subject/certificate", access_token=access_token, json=request)

    async def reset_certificate_limits(self, *, access_token: str) -> None:
        await self._base.delete("testdata/limits/subject/certificate", access_token=access_token)

    async def change_rate_limits(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/rate-limits", access_token=access_token, json=request)

    async def reset_rate_limits(self, *, access_token: str) -> None:
        await self._base.delete("testdata/rate-limits", access_token=access_token)

    async def set_production_rate_limits(self, *, access_token: str) -> dict:
        return await self._base.post("testdata/rate-limits/production", access_token=access_token)

    async def block_context(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/context/block", access_token=access_token, json=request)

    async def unblock_context(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/context/unblock", access_token=access_token, json=request)
