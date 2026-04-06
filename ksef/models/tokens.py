from __future__ import annotations

from datetime import datetime

from ksef.models.common import KSeFModel, OperationStatusInfo


class KSeFTokenGenerateRequest(KSeFModel):
    permissions: list[str]
    description: str


class KSeFTokenResponse(KSeFModel):
    reference_number: str
    token: str


class KSeFTokenInfo(KSeFModel):
    reference_number: str
    author_identifier: dict | None = None
    context_identifier: dict | None = None
    description: str = ""
    requested_permissions: list[str] = []
    date_created: datetime | None = None
    last_use_date: datetime | None = None
    status: OperationStatusInfo | None = None
    status_details: list[dict] | None = None


class KSeFTokenListResponse(KSeFModel):
    tokens: list[KSeFTokenInfo] = []
    continuation_token: str | None = None
