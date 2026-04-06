from __future__ import annotations
from typing import Any
from ksef.client.base import BaseClient


class PermissionClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def grant_person(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/persons/grants", access_token=access_token, json=request)

    async def grant_entity(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/entities/grants", access_token=access_token, json=request)

    async def grant_authorization(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/authorizations/grants", access_token=access_token, json=request)

    async def grant_indirect(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/indirect/grants", access_token=access_token, json=request)

    async def grant_subunit(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/subunits/grants", access_token=access_token, json=request)

    async def grant_eu_entity(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/eu-entities/administration/grants", access_token=access_token, json=request)

    async def grant_eu_representative(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/eu-entities/grants", access_token=access_token, json=request)

    async def revoke_common(self, permission_id: str, *, access_token: str) -> None:
        await self._base.delete(f"permissions/common/grants/{permission_id}", access_token=access_token)

    async def revoke_authorization(self, permission_id: str, *, access_token: str) -> None:
        await self._base.delete(f"permissions/authorizations/grants/{permission_id}", access_token=access_token)

    async def query_personal(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/personal/grants", access_token=access_token, json=request)

    async def query_persons(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/persons/grants", access_token=access_token, json=request)

    async def query_entities(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/entities/grants", access_token=access_token, json=request)

    async def query_subunits(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/subunits/grants", access_token=access_token, json=request)

    async def query_authorizations(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/authorizations/grants", access_token=access_token, json=request)

    async def query_eu_entities(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/eu-entities/grants", access_token=access_token, json=request)

    async def query_entity_roles(self, *, access_token: str) -> dict:
        return await self._base.get("permissions/query/entities/roles", access_token=access_token)

    async def query_subordinate_roles(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/subordinate-entities/roles", access_token=access_token, json=request)

    async def get_operation_status(self, reference_number: str, *, access_token: str) -> dict:
        return await self._base.get(f"permissions/operations/{reference_number}", access_token=access_token)

    async def get_attachment_status(self, *, access_token: str) -> dict:
        return await self._base.get("permissions/attachments/status", access_token=access_token)
