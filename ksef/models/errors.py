from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from ksef.models.common import KSeFModel


class ExceptionDetail(KSeFModel):
    exception_code: int
    exception_description: str


class ExceptionContent(KSeFModel):
    service_ctx: str | None = None
    service_code: str | None = None
    service_name: str | None = None
    timestamp: str | None = None
    reference_number: str | None = None
    exception_detail_list: list[ExceptionDetail] = []


class ApiErrorResponse(KSeFModel):
    exception: ExceptionContent


class ProblemDetails(BaseModel):
    """RFC 7807 Problem Details."""
    model_config = ConfigDict(populate_by_name=True)
    type: str | None = None
    title: str | None = None
    status: int | None = None
    detail: str | None = None
    instance: str | None = None
