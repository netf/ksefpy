from __future__ import annotations

from ksef.client.base import BaseClient
from ksef.models.auth import (
    AuthenticationChallengeResponse,
    AuthenticationKsefTokenRequest,
    AuthenticationOperationStatusResponse,
    RefreshTokenResponse,
    SignatureResponse,
)


class AuthClient:
    """Client for KSeF authentication endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def get_challenge(self) -> AuthenticationChallengeResponse:
        """POST /auth/challenge"""
        data = await self._base.post("auth/challenge")
        return AuthenticationChallengeResponse.model_validate(data)

    async def submit_xades_signature(
        self,
        signed_xml: str,
        *,
        access_token: str | None = None,
        verify_certificate_chain: bool = False,
        enforce_xades_compliance: bool = False,
    ) -> SignatureResponse:
        """POST /auth/xades-signature"""
        extra_headers: dict[str, str] = {"Content-Type": "application/xml"}
        if enforce_xades_compliance:
            extra_headers["X-KSeF-Feature"] = "enforce-xades-compliance"
        data = await self._base.post(
            "auth/xades-signature",
            access_token=access_token,
            content=signed_xml.encode("utf-8"),
            headers=extra_headers,
        )
        return SignatureResponse.model_validate(data)

    async def submit_ksef_token(
        self,
        request: AuthenticationKsefTokenRequest,
    ) -> SignatureResponse:
        """POST /auth/ksef-token"""
        data = await self._base.post("auth/ksef-token", json=request.model_dump(by_alias=True, exclude_none=True))
        return SignatureResponse.model_validate(data)

    async def get_auth_status(
        self,
        reference_number: str,
        *,
        authentication_token: str,
    ) -> dict:
        """GET /auth/{referenceNumber}"""
        return await self._base.get(f"auth/{reference_number}", access_token=authentication_token)

    async def redeem_token(self, *, authentication_token: str) -> AuthenticationOperationStatusResponse:
        """POST /auth/token/redeem"""
        data = await self._base.post("auth/token/redeem", access_token=authentication_token)
        return AuthenticationOperationStatusResponse.model_validate(data)

    async def refresh_token(self, *, refresh_token: str) -> RefreshTokenResponse:
        """POST /auth/token/refresh"""
        data = await self._base.post("auth/token/refresh", access_token=refresh_token)
        return RefreshTokenResponse.model_validate(data)
