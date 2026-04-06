from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class KSeFModel(BaseModel):
    """Base model with camelCase alias generation."""
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda field_name: "".join(
            word.capitalize() if i > 0 else word for i, word in enumerate(field_name.split("_"))
        ),
    )


class ContextIdentifierType(StrEnum):
    NIP = "nip"
    INTERNAL_ID = "onip"
    EU_VAT = "nipVatUe"


class ContextIdentifier(KSeFModel):
    type: ContextIdentifierType
    value: str


class OperationStatusInfo(KSeFModel):
    code: str
    description: str | None = None


class PaginationParams(KSeFModel):
    page: int = 0
    page_size: int = 10
