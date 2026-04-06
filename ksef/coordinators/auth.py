"""Authentication workflow coordinator for KSeF."""

from __future__ import annotations

import asyncio
import base64
import datetime
import time
from typing import TYPE_CHECKING

from ksef.exceptions import KSeFTimeoutError
from ksef.models.auth import AuthenticationKsefTokenRequest, TokenInfo
from ksef.models.common import ContextIdentifier, ContextIdentifierType

if TYPE_CHECKING:
    from ksef.client import AsyncKSeFClient
    from ksef.crypto.service import CryptographyService


class AuthSession:
    """Manages access/refresh token lifecycle with automatic refresh."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        access_token: TokenInfo,
        refresh_token: TokenInfo,
        refresh_buffer: float = 60.0,
    ) -> None:
        self._client = client
        self._access_token_info = access_token
        self._refresh_token_info = refresh_token
        self._refresh_buffer = refresh_buffer
        self._lock = asyncio.Lock()

    @property
    def access_token_info(self) -> TokenInfo:
        return self._access_token_info

    @property
    def refresh_token_info(self) -> TokenInfo:
        return self._refresh_token_info

    def _is_near_expiry(self, token: TokenInfo) -> bool:
        """Return True if token expires within refresh_buffer seconds."""
        now = datetime.datetime.now(datetime.UTC)
        valid_until = token.valid_until
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=datetime.UTC)
        remaining = (valid_until - now).total_seconds()
        return remaining <= self._refresh_buffer

    async def get_access_token(self) -> str:
        """Return the current access token, auto-refreshing if near expiry."""
        async with self._lock:
            if self._is_near_expiry(self._access_token_info):
                refresh_resp = await self._client.auth.refresh_token(
                    refresh_token=self._refresh_token_info.token
                )
                self._access_token_info = refresh_resp.access_token
            return self._access_token_info.token


class AsyncAuthCoordinator:
    """Orchestrates full KSeF authentication flows."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        crypto: CryptographyService | None = None,
    ) -> None:
        self._client = client
        self._crypto = crypto
        self._crypto_warmed_up = False

    async def _get_or_create_crypto(self) -> CryptographyService:
        from ksef.crypto.service import CryptographyService

        if self._crypto is None:
            self._crypto = CryptographyService()
        if not self._crypto_warmed_up:
            await self._warmup_crypto(self._crypto)
            self._crypto_warmed_up = True
        return self._crypto

    async def _warmup_crypto(self, crypto: CryptographyService) -> None:
        """Fetch public-key certificates from API and set them on crypto service."""
        from cryptography import x509 as _x509

        data = await self._client._base.get("security/public-key-certificates")

        # API returns a list of cert objects with usage flags
        if isinstance(data, list):
            for item in data:
                cert_b64 = item.get("certificate", "")
                usages = item.get("usage", [])
                if not cert_b64:
                    continue
                cert_der = base64.b64decode(cert_b64)
                cert = _x509.load_der_x509_certificate(cert_der)
                if "SYMMETRIC_KEY_ENCRYPTION" in usages:
                    crypto.set_symmetric_key_certificate(cert)
                if "KSEF_TOKEN_ENCRYPTION" in usages:
                    crypto.set_ksef_token_certificate(cert)
        elif isinstance(data, dict):
            # Legacy dict format
            raw_sym = data.get("symmetricKeyEncryptionCertificate") or data.get("symmetricKey")
            raw_tok = data.get("tokenEncryptionCertificate") or data.get("token")
            if raw_sym:
                crypto.set_symmetric_key_certificate(
                    _x509.load_pem_x509_certificate(
                        raw_sym.encode() if isinstance(raw_sym, str) else raw_sym
                    )
                )
            if raw_tok:
                crypto.set_ksef_token_certificate(
                    _x509.load_pem_x509_certificate(
                        raw_tok.encode() if isinstance(raw_tok, str) else raw_tok
                    )
                )

    async def _poll_auth_status(
        self,
        reference_number: str,
        authentication_token: str,
        *,
        poll_interval: float,
        poll_timeout: float,
    ) -> None:
        """Poll auth status until it reports success (code 200) or timeout."""
        deadline = time.monotonic() + poll_timeout
        while True:
            status_data = await self._client.auth.get_auth_status(
                reference_number,
                authentication_token=authentication_token,
            )
            code = None
            if isinstance(status_data, dict):
                status = status_data.get("status", {})
                if isinstance(status, dict):
                    code = status.get("code")
            if str(code) == "200":
                return
            if time.monotonic() >= deadline:
                raise KSeFTimeoutError(
                    f"Authentication polling timed out after {poll_timeout}s"
                )
            await asyncio.sleep(poll_interval)

    async def authenticate_with_token(
        self,
        nip: str,
        ksef_token: str,
        *,
        poll_interval: float = 1.0,
        poll_timeout: float = 120.0,
        refresh_buffer: float = 60.0,
    ) -> AuthSession:
        """Authenticate using a KSeF API token.

        Flow: warmup crypto -> get_challenge -> encrypt_ksef_token ->
              submit_ksef_token -> poll get_auth_status -> redeem_token
        """
        crypto = await self._get_or_create_crypto()

        challenge_resp = await self._client.auth.get_challenge()

        encrypted_token = crypto.encrypt_ksef_token(
            token=ksef_token,
            timestamp_ms=challenge_resp.timestamp_ms,
        )

        auth_request = AuthenticationKsefTokenRequest(
            challenge=challenge_resp.challenge,
            context_identifier=ContextIdentifier(
                type=ContextIdentifierType.NIP,
                value=nip,
            ),
            encrypted_token=encrypted_token,
        )
        signature_resp = await self._client.auth.submit_ksef_token(auth_request)

        reference_number = signature_resp.reference_number
        authentication_token = signature_resp.authentication_token.token

        await self._poll_auth_status(
            reference_number,
            authentication_token,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )

        redeem_resp = await self._client.auth.redeem_token(
            authentication_token=authentication_token
        )

        return AuthSession(
            client=self._client,
            access_token=redeem_resp.access_token,
            refresh_token=redeem_resp.refresh_token,
            refresh_buffer=refresh_buffer,
        )

    async def authenticate_with_certificate(
        self,
        nip: str,
        *,
        certificate_path: str | None = None,
        certificate: bytes | None = None,
        private_key_path: str | None = None,
        private_key: bytes | None = None,
        poll_interval: float = 1.0,
        poll_timeout: float = 120.0,
        refresh_buffer: float = 60.0,
    ) -> AuthSession:
        """Authenticate using an X.509 certificate with XAdES signature.

        Flow: get_challenge -> build auth XML -> XAdES sign ->
              submit_xades_signature -> poll -> redeem
        """
        from ksef.crypto.xades import XAdESService

        # Load certificate bytes
        if certificate is None:
            if certificate_path is None:
                raise ValueError("Either certificate or certificate_path must be provided")
            with open(certificate_path, "rb") as f:
                certificate = f.read()

        # Load private key bytes
        if private_key is None:
            if private_key_path is None:
                raise ValueError("Either private_key or private_key_path must be provided")
            with open(private_key_path, "rb") as f:
                private_key = f.read()

        challenge_resp = await self._client.auth.get_challenge()

        # Build the AuthTokenRequest XML document
        auth_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<AuthTokenRequest xmlns="http://ksef.mf.gov.pl/schema/auth">'
            f"<Challenge>{challenge_resp.challenge}</Challenge>"
            f"<Identifier><Type>nip</Type><Value>{nip}</Value></Identifier>"
            "</AuthTokenRequest>"
        )

        xades_service = XAdESService()
        signed_xml = xades_service.sign(
            auth_xml,
            certificate=certificate,
            private_key=private_key,
        )

        signature_resp = await self._client.auth.submit_xades_signature(signed_xml)

        reference_number = signature_resp.reference_number
        authentication_token = signature_resp.authentication_token.token

        await self._poll_auth_status(
            reference_number,
            authentication_token,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )

        redeem_resp = await self._client.auth.redeem_token(
            authentication_token=authentication_token
        )

        return AuthSession(
            client=self._client,
            access_token=redeem_resp.access_token,
            refresh_token=redeem_resp.refresh_token,
            refresh_buffer=refresh_buffer,
        )
