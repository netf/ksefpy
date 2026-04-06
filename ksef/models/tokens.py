from __future__ import annotations

from datetime import datetime

from ksef.models.common import ContextIdentifier, KSeFModel


class KSeFTokenGenerateRequest(KSeFModel):
    context_identifier: ContextIdentifier
    permissions: list[str]
    description: str | None = None


class KSeFTokenResponse(KSeFModel):
    reference_number: str


class KSeFTokenInfo(KSeFModel):
    reference_number: str
    description: str | None = None
    status: str | None = None
    permissions: list[str] = []
    date_created: datetime | None = None


class KSeFTokenListResponse(KSeFModel):
    items: list[KSeFTokenInfo] = []
    continuation_token: str | None = None
