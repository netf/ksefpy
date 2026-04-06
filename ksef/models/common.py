from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


def _to_camel(field_name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = field_name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class KSeFModel(BaseModel):
    """Base model with camelCase alias generation."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)


class ContextIdentifierType(StrEnum):
    NIP = "nip"
    INTERNAL_ID = "onip"
    EU_VAT = "nipVatUe"


class ContextIdentifier(KSeFModel):
    type: ContextIdentifierType
    value: str


class OperationStatusInfo(KSeFModel):
    code: int
    description: str
    details: list[str] = []


