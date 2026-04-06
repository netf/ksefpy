"""High-level KSeF API — single-class facade over all internal components.

Usage::

    async with AsyncKSeF("1234567890", token="your-token", env="test") as ksef:
        result = await ksef.send_invoice(xml_bytes)
        print(result.reference_number)
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ksef.crypto.service import CryptographyService

from ksef._types import InvoiceResult, LimitsInfo, SessionStatus, TokenResult
from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AsyncAuthCoordinator, AuthSession
from ksef.coordinators.online_session import AsyncOnlineSessionManager, OnlineSessionContext
from ksef.environments import Environment
from ksef.exceptions import (
    KSeFAuthError,
    KSeFError,
    KSeFInvoiceError,
    KSeFPermissionError,
    KSeFRateLimitError,
    KSeFServerError,
    _ApiError,
)

# ---------------------------------------------------------------------------
# Error mapping: _ApiError -> public exceptions
# ---------------------------------------------------------------------------


def _map_api_error(exc: _ApiError) -> KSeFError:
    """Convert an internal ``_ApiError`` to the appropriate public exception."""
    status = exc.status_code
    raw = exc.raw_response
    msg = str(exc)

    if status == 401:
        return KSeFAuthError(msg, raw_response=raw)
    if status == 403:
        return KSeFPermissionError(msg, raw_response=raw)
    if status == 429:
        return KSeFRateLimitError(msg, retry_after=exc.retry_after, raw_response=raw)
    if status >= 500:
        return KSeFServerError(msg, status_code=status, raw_response=raw)
    if status in (400, 450):
        return KSeFInvoiceError(msg, raw_response=raw)

    # Fallback
    return KSeFError(msg, raw_response=raw)


# ---------------------------------------------------------------------------
# Environment resolution
# ---------------------------------------------------------------------------

_ENV_MAP: dict[str, Environment] = {
    "production": Environment.PRODUCTION,
    "prod": Environment.PRODUCTION,
    "demo": Environment.DEMO,
    "test": Environment.TEST,
}


def _resolve_env(env: str | Environment) -> Environment:
    """Resolve a string or Environment object to an Environment."""
    if isinstance(env, Environment):
        return env
    key = env.lower().strip()
    if key not in _ENV_MAP:
        raise ValueError(
            f"Unknown environment {env!r}. Use one of: {', '.join(sorted(_ENV_MAP))} or pass an Environment object."
        )
    return _ENV_MAP[key]


# ---------------------------------------------------------------------------
# AsyncSessionContext — multi-send wrapper
# ---------------------------------------------------------------------------


class AsyncSessionContext:
    """Context manager for multi-invoice session operations.

    Usage::

        async with ksef.session() as s:
            await s.send(xml1)
            await s.send(xml2)
        print(s.results)
    """

    def __init__(self, online_ctx: OnlineSessionContext) -> None:
        self._ctx = online_ctx
        self.results: list[InvoiceResult] = []

    @property
    def reference_number(self) -> str:
        """The session reference number."""
        return self._ctx.reference_number

    async def send(self, xml: bytes, *, offline: bool = False) -> InvoiceResult:
        """Send a single invoice within the open session."""
        try:
            resp = await self._ctx.send_invoice_xml(xml, offline_mode=offline)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc
        result = InvoiceResult(
            reference_number=resp.reference_number,
        )
        self.results.append(result)
        return result


# ---------------------------------------------------------------------------
# AsyncKSeF — the main high-level class
# ---------------------------------------------------------------------------


class AsyncKSeF:
    """High-level async KSeF client.

    Provides a simple, opinionated API over the full KSeF workflow:
    authentication, session management, invoice sending/downloading,
    token management, permissions, and more.

    Parameters
    ----------
    nip:
        Polish tax identifier (NIP) of the entity.
    token:
        KSeF API token for token-based authentication.
    cert:
        X.509 certificate bytes (PEM) for certificate-based authentication.
    key:
        Private key bytes (PEM) for certificate-based authentication.
    env:
        Target environment — ``"production"``, ``"demo"``, ``"test"``,
        or an :class:`Environment` object.
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        nip: str,
        *,
        token: str | None = None,
        cert: bytes | None = None,
        key: bytes | None = None,
        env: str | Environment = "production",
        timeout: float = 30.0,
    ) -> None:
        if not nip:
            raise ValueError("nip is required")
        if not (nip.isdigit() and len(nip) == 10):
            raise ValueError(f"nip must be exactly 10 digits, got: {nip!r}")
        if token and (cert or key):
            raise ValueError("Provide either token OR (cert + key), not both")
        if not token and not (cert and key):
            raise ValueError("Provide token or (cert + key) for authentication")
        if (cert is None) != (key is None):
            raise ValueError("Both cert and key must be provided together")

        self._nip = nip
        self._token = token
        self._cert = cert
        self._key = key
        self._environment = _resolve_env(env)
        self._timeout = timeout

        # Internal state — created eagerly
        self._client = AsyncKSeFClient(environment=self._environment, timeout=timeout)
        self._auth_coordinator = AsyncAuthCoordinator(self._client)

        # Set after first authentication
        self._auth_session: AuthSession | None = None
        self._crypto: CryptographyService | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> AsyncKSeF:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()

    # ------------------------------------------------------------------
    # Lazy authentication
    # ------------------------------------------------------------------

    async def _ensure_auth(self) -> None:
        """Authenticate lazily on first use."""
        if self._auth_session is not None:
            return
        try:
            if self._token:
                self._auth_session = await self._auth_coordinator.authenticate_with_token(
                    nip=self._nip,
                    ksef_token=self._token,
                )
            else:
                assert self._cert is not None and self._key is not None
                self._auth_session = await self._auth_coordinator.authenticate_with_certificate(
                    nip=self._nip,
                    certificate=self._cert,
                    private_key=self._key,
                )
            self._crypto = await self._auth_coordinator._get_or_create_crypto()
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    async def _get_access_token(self) -> str:
        """Return a valid access token, refreshing if needed.

        If the refresh token has expired, re-authenticates from scratch.
        """
        await self._ensure_auth()
        assert self._auth_session is not None
        try:
            return await self._auth_session.get_access_token()
        except KSeFError:
            # Session expired — force re-authentication
            self._auth_session = None
            self._crypto = None
            await self._ensure_auth()
            assert self._auth_session is not None
            return await self._auth_session.get_access_token()

    # ------------------------------------------------------------------
    # Invoice operations
    # ------------------------------------------------------------------

    async def send_invoice(self, xml: bytes, *, offline: bool = False, schema: str = "FA(3)") -> InvoiceResult:
        """Send a single invoice.

        Opens a session, sends the invoice, closes the session, and
        returns an :class:`InvoiceResult`.
        """
        await self._ensure_auth()
        assert self._auth_session is not None
        try:
            mgr = AsyncOnlineSessionManager(
                self._client,
                self._auth_session,
                crypto=self._crypto,
            )
            async with mgr.open(schema) as ctx:
                resp = await ctx.send_invoice_xml(xml, offline_mode=offline)
                ref = resp.reference_number
            return InvoiceResult(reference_number=ref)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    async def send_invoices(
        self, xmls: list[bytes], *, offline: bool = False, schema: str = "FA(3)"
    ) -> list[InvoiceResult]:
        """Send multiple invoices in a single session.

        Opens one session, sends all invoices, closes the session, and
        returns a list of :class:`InvoiceResult`.
        """
        await self._ensure_auth()
        assert self._auth_session is not None
        results: list[InvoiceResult] = []
        try:
            mgr = AsyncOnlineSessionManager(
                self._client,
                self._auth_session,
                crypto=self._crypto,
            )
            async with mgr.open(schema) as ctx:
                for xml in xmls:
                    resp = await ctx.send_invoice_xml(xml, offline_mode=offline)
                    results.append(InvoiceResult(reference_number=resp.reference_number))
            return results
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    @asynccontextmanager
    async def session(self, schema: str = "FA(3)") -> AsyncGenerator[AsyncSessionContext, None]:
        """Open an interactive session for sending multiple invoices.

        Usage::

            async with ksef.session() as s:
                await s.send(xml1)
                await s.send(xml2)
            print(s.results)
        """
        await self._ensure_auth()
        assert self._auth_session is not None
        mgr = AsyncOnlineSessionManager(
            self._client,
            self._auth_session,
            crypto=self._crypto,
        )
        try:
            async with mgr.open(schema) as online_ctx:
                sess_ctx = AsyncSessionContext(online_ctx)
                yield sess_ctx
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    # ------------------------------------------------------------------
    # Invoice download / query / export
    # ------------------------------------------------------------------

    async def download_invoice(self, ksef_number: str) -> bytes:
        """Download a single invoice by its KSeF number. Returns raw XML bytes."""
        access_token = await self._get_access_token()
        try:
            return await self._client.invoices.download(ksef_number, access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    async def query_invoices(self, **filters: Any) -> dict:
        """Query invoice metadata with the given filters.

        Passes *filters* as the JSON body to the metadata query endpoint.
        """
        access_token = await self._get_access_token()
        try:
            return await self._client.invoices.query_metadata(filters, access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    async def export_invoices(self, **filters: Any) -> dict:
        """Request an invoice export. Returns the raw API response.

        Automatically adds ``encryption`` and wraps filters in the
        ``filters`` key expected by the API.
        """
        await self._ensure_auth()
        assert self._crypto is not None
        access_token = await self._get_access_token()

        from ksef.models.sessions import EncryptionInfo

        materials = self._crypto.generate_session_materials()
        enc = EncryptionInfo.from_session_materials(materials)
        body: dict[str, Any] = {
            "filters": filters,
            "encryption": enc.model_dump(by_alias=True),
        }
        try:
            return await self._client.invoices.export(body, access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    async def create_token(self, permissions: list[str], description: str = "") -> TokenResult:
        """Create a new KSeF API token.

        Returns a :class:`TokenResult` with the reference number and token value.
        """
        access_token = await self._get_access_token()
        request: dict[str, Any] = {"permissions": permissions}
        if description:
            request["description"] = description
        try:
            data = await self._client.tokens.generate(request, access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc
        return TokenResult(
            reference_number=data.get("referenceNumber", ""),
            token=data.get("token", ""),
        )

    async def list_tokens(self) -> dict:
        """List all API tokens for the authenticated entity."""
        access_token = await self._get_access_token()
        try:
            return await self._client.tokens.list_tokens(access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    async def revoke_token(self, reference: str) -> None:
        """Revoke an API token by its reference number."""
        access_token = await self._get_access_token()
        try:
            await self._client.tokens.revoke(reference, access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    async def query_permissions(self, **filters: Any) -> dict:
        """Query personal permissions for the authenticated entity."""
        access_token = await self._get_access_token()
        try:
            return await self._client.permissions.query_personal(
                filters or {},
                access_token=access_token,
            )
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    async def get_attachment_status(self) -> dict:
        """Get the attachment status for the authenticated entity."""
        access_token = await self._get_access_token()
        try:
            return await self._client.permissions.get_attachment_status(access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    # ------------------------------------------------------------------
    # Certificates
    # ------------------------------------------------------------------

    async def get_certificate_limits(self) -> dict:
        """Get certificate limits for the authenticated entity."""
        access_token = await self._get_access_token()
        try:
            return await self._client.certificates.get_limits(access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    async def get_enrollment_data(self) -> dict:
        """Get enrollment data for the authenticated entity."""
        access_token = await self._get_access_token()
        try:
            return await self._client.certificates.get_enrollment_data(access_token=access_token)
        except _ApiError as exc:
            raise _map_api_error(exc) from exc

    # ------------------------------------------------------------------
    # Limits
    # ------------------------------------------------------------------

    async def get_limits(self) -> LimitsInfo:
        """Fetch context, subject, and rate limits in parallel.

        Returns a :class:`LimitsInfo` dataclass with all three.
        """
        access_token = await self._get_access_token()
        try:
            context_data, subject_data, rate_data = await asyncio.gather(
                self._client.limits.get_context_limits(access_token=access_token),
                self._client.limits.get_subject_limits(access_token=access_token),
                self._client.limits.get_rate_limits(access_token=access_token),
            )
        except _ApiError as exc:
            raise _map_api_error(exc) from exc
        return LimitsInfo(
            context=context_data if isinstance(context_data, dict) else {},
            subject=subject_data if isinstance(subject_data, dict) else {},
            rate=rate_data if isinstance(rate_data, dict) else {},
        )

    # ------------------------------------------------------------------
    # Session status
    # ------------------------------------------------------------------

    async def get_session_status(self, reference: str) -> SessionStatus:
        """Get session status by reference number.

        Returns a :class:`SessionStatus` dataclass.
        """
        access_token = await self._get_access_token()
        try:
            resp = await self._client.session_status.get_session_status(
                reference,
                access_token=access_token,
            )
        except _ApiError as exc:
            raise _map_api_error(exc) from exc
        return SessionStatus(
            code=resp.status.code,
            description=resp.status.description,
            invoice_count=resp.invoice_count,
            successful_count=resp.successful_invoice_count,
            failed_count=resp.failed_invoice_count,
        )

    # ------------------------------------------------------------------
    # QR code
    # ------------------------------------------------------------------

    def qr_url(self, invoice_date: date, seller_nip: str, file_hash: str) -> str:
        """Build a KSeF QR Code Type 1 verification URL.

        Parameters
        ----------
        invoice_date:
            Issue date of the invoice.
        seller_nip:
            Seller's NIP (tax identifier).
        file_hash:
            Base64URL-encoded SHA-256 hash of the structured invoice file.
        """
        from ksef.crypto.qr import build_qr_code_1_url

        return build_qr_code_1_url(
            environment=self._environment,
            invoice_date=invoice_date,
            seller_nip=seller_nip,
            file_sha256_b64url=file_hash,
        )
