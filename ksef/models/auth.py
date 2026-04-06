from __future__ import annotations
from datetime import datetime
from ksef.models.common import ContextIdentifier, KSeFModel


class TokenInfo(KSeFModel):
    token: str
    valid_until: datetime


class AuthenticationChallengeResponse(KSeFModel):
    challenge: str
    timestamp: datetime
    timestamp_ms: int
    client_ip: str | None = None


class AuthenticationKsefTokenRequest(KSeFModel):
    challenge: str
    context_identifier: ContextIdentifier
    encrypted_token: str
    authorization_policy: dict | None = None


class SignatureResponse(KSeFModel):
    reference_number: str
    authentication_token: TokenInfo


class AuthenticationOperationStatusResponse(KSeFModel):
    access_token: TokenInfo
    refresh_token: TokenInfo


class RefreshTokenResponse(KSeFModel):
    access_token: TokenInfo
