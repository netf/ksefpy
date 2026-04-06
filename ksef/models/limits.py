from __future__ import annotations
from ksef.models.common import KSeFModel


class ContextLimits(KSeFModel):
    max_online_sessions: int | None = None
    max_batch_sessions: int | None = None
    active_online_sessions: int | None = None
    active_batch_sessions: int | None = None


class SubjectLimits(KSeFModel):
    max_certificates: int | None = None
    active_certificates: int | None = None


class RateLimitEntry(KSeFModel):
    group: str | None = None
    per_second: int | None = None
    per_minute: int | None = None
    per_hour: int | None = None


class RateLimitsResponse(KSeFModel):
    limits: list[RateLimitEntry] = []
