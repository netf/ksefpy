from __future__ import annotations

from ksef.models.common import ContextIdentifier, KSeFModel, OperationStatusInfo


class EntityPermission(KSeFModel):
    type: str
    can_delegate: bool = False


class PersonPermissionGrantRequest(KSeFModel):
    subject_identifier: ContextIdentifier
    permissions: list[str]
    description: str
    subject_details: dict


class EntityPermissionGrantRequest(KSeFModel):
    subject_identifier: ContextIdentifier
    permissions: list[EntityPermission]
    description: str
    subject_details: dict


class PermissionOperationStatusResponse(KSeFModel):
    status: OperationStatusInfo


class PermissionGrantResponse(KSeFModel):
    reference_number: str
