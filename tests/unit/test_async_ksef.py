"""Unit tests for AsyncKSeF — the public high-level API.

Tests constructor validation, environment resolution, error mapping,
and method behavior with mocked internals.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from ksef._client import AsyncKSeF, _map_api_error, _resolve_env
from ksef._types import InvoiceResult, LimitsInfo, SessionStatus, TokenResult
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
# Constructor validation
# ---------------------------------------------------------------------------


class TestConstructorValidation:
    def test_requires_nip(self):
        with pytest.raises(ValueError, match="nip is required"):
            AsyncKSeF(nip="", token="tok")

    def test_requires_auth_method(self):
        with pytest.raises(ValueError, match="token or"):
            AsyncKSeF(nip="1234567890")

    def test_rejects_both_token_and_cert(self):
        with pytest.raises(ValueError, match="either token OR"):
            AsyncKSeF(nip="1234567890", token="tok", cert=b"c", key=b"k")

    def test_cert_requires_key(self):
        with pytest.raises(ValueError, match="token or"):
            AsyncKSeF(nip="1234567890", cert=b"cert")

    def test_key_requires_cert(self):
        with pytest.raises(ValueError, match="token or"):
            AsyncKSeF(nip="1234567890", key=b"key")

    def test_valid_token_auth(self):
        client = AsyncKSeF(nip="1234567890", token="my-token", env="test")
        assert client._nip == "1234567890"
        assert client._token == "my-token"
        assert client._cert is None
        assert client._environment == Environment.TEST

    def test_valid_cert_auth(self):
        client = AsyncKSeF(nip="1234567890", cert=b"cert", key=b"key", env="demo")
        assert client._cert == b"cert"
        assert client._key == b"key"
        assert client._token is None
        assert client._environment == Environment.DEMO

    def test_default_env_is_production(self):
        client = AsyncKSeF(nip="1234567890", token="tok")
        assert client._environment == Environment.PRODUCTION

    def test_custom_timeout(self):
        client = AsyncKSeF(nip="1234567890", token="tok", timeout=60.0)
        assert client._timeout == 60.0


# ---------------------------------------------------------------------------
# Environment resolution
# ---------------------------------------------------------------------------


class TestResolveEnv:
    def test_string_test(self):
        assert _resolve_env("test") == Environment.TEST

    def test_string_demo(self):
        assert _resolve_env("demo") == Environment.DEMO

    def test_string_production(self):
        assert _resolve_env("production") == Environment.PRODUCTION

    def test_string_prod_shorthand(self):
        assert _resolve_env("prod") == Environment.PRODUCTION

    def test_case_insensitive(self):
        assert _resolve_env("TEST") == Environment.TEST
        assert _resolve_env("Demo") == Environment.DEMO

    def test_strips_whitespace(self):
        assert _resolve_env("  test  ") == Environment.TEST

    def test_environment_passthrough(self):
        assert _resolve_env(Environment.DEMO) == Environment.DEMO

    def test_invalid_string(self):
        with pytest.raises(ValueError, match="Unknown environment"):
            _resolve_env("staging")


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


class TestMapApiError:
    def test_401_maps_to_auth_error(self):
        exc = _ApiError("unauthorized", status_code=401, raw_response={"detail": "bad token"})
        mapped = _map_api_error(exc)
        assert isinstance(mapped, KSeFAuthError)
        assert mapped.raw_response == {"detail": "bad token"}

    def test_403_maps_to_permission_error(self):
        mapped = _map_api_error(_ApiError("forbidden", status_code=403))
        assert isinstance(mapped, KSeFPermissionError)

    def test_429_maps_to_rate_limit_error(self):
        exc = _ApiError("too many", status_code=429, retry_after=30.0)
        mapped = _map_api_error(exc)
        assert isinstance(mapped, KSeFRateLimitError)
        assert mapped.retry_after == 30.0

    def test_500_maps_to_server_error(self):
        mapped = _map_api_error(_ApiError("server down", status_code=502))
        assert isinstance(mapped, KSeFServerError)
        assert mapped.status_code == 502

    def test_400_maps_to_invoice_error(self):
        mapped = _map_api_error(_ApiError("bad request", status_code=400))
        assert isinstance(mapped, KSeFInvoiceError)

    def test_450_maps_to_invoice_error(self):
        mapped = _map_api_error(_ApiError("semantic error", status_code=450))
        assert isinstance(mapped, KSeFInvoiceError)

    def test_unknown_status_maps_to_base_error(self):
        mapped = _map_api_error(_ApiError("weird", status_code=418))
        assert type(mapped) is KSeFError

    def test_all_mapped_errors_are_ksef_error(self):
        for code in [400, 401, 403, 418, 429, 450, 500, 502, 503]:
            mapped = _map_api_error(_ApiError("test", status_code=code))
            assert isinstance(mapped, KSeFError)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


class TestResultTypes:
    def test_invoice_result_defaults(self):
        r = InvoiceResult(reference_number="ref-1")
        assert r.reference_number == "ref-1"
        assert r.ksef_number is None
        assert r.status == "sent"

    def test_invoice_result_full(self):
        r = InvoiceResult(reference_number="ref-1", ksef_number="ksef-1", status="accepted")
        assert r.ksef_number == "ksef-1"
        assert r.status == "accepted"

    def test_token_result(self):
        r = TokenResult(reference_number="ref-1", token="tok-abc")
        assert r.reference_number == "ref-1"
        assert r.token == "tok-abc"

    def test_limits_info_defaults(self):
        r = LimitsInfo()
        assert r.context == {}
        assert r.subject == {}
        assert r.rate == {}

    def test_limits_info_with_data(self):
        r = LimitsInfo(context={"a": 1}, subject={"b": 2}, rate={"c": 3})
        assert r.context["a"] == 1

    def test_session_status(self):
        r = SessionStatus(code=200, description="OK", invoice_count=5, successful_count=4, failed_count=1)
        assert r.code == 200
        assert r.invoice_count == 5
        assert r.successful_count == 4
        assert r.failed_count == 1

    def test_session_status_defaults(self):
        r = SessionStatus(code=100, description="Processing")
        assert r.invoice_count is None
        assert r.successful_count is None
        assert r.failed_count is None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_ksef_error_base(self):
        exc = KSeFError("something broke")
        assert str(exc) == "something broke"
        assert exc.raw_response == {}

    def test_ksef_error_with_raw_response(self):
        exc = KSeFError("broke", raw_response={"code": 123})
        assert "raw_response=" in str(exc)
        assert exc.raw_response["code"] == 123

    def test_auth_error_inherits(self):
        exc = KSeFAuthError("bad auth")
        assert isinstance(exc, KSeFError)

    def test_rate_limit_with_retry_after(self):
        exc = KSeFRateLimitError("slow down", retry_after=30.0)
        assert exc.retry_after == 30.0
        assert "retry_after=30.0" in str(exc)

    def test_server_error_with_status_code(self):
        exc = KSeFServerError("down", status_code=503)
        assert exc.status_code == 503

    def test_all_exceptions_are_ksef_error(self):
        for cls in [KSeFAuthError, KSeFInvoiceError, KSeFPermissionError, KSeFServerError]:
            assert issubclass(cls, KSeFError)


# ---------------------------------------------------------------------------
# AsyncKSeF methods (mocked internals)
# ---------------------------------------------------------------------------


class TestAsyncKSeFMethods:
    @pytest.fixture
    def client(self):
        return AsyncKSeF(nip="1234567890", token="test-token", env="test")

    @pytest.mark.asyncio
    async def test_close(self, client):
        client._client = AsyncMock()
        await client.close()
        client._client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with AsyncKSeF(nip="1234567890", token="tok", env="test") as client:
            client._client = AsyncMock()
        # __aexit__ calls close

    @pytest.mark.asyncio
    async def test_ensure_auth_lazy(self, client):
        """_ensure_auth does nothing if already authenticated."""
        client._auth_session = MagicMock()  # pretend already authed
        await client._ensure_auth()
        # No error, no network call

    @pytest.mark.asyncio
    async def test_qr_url(self, client):
        url = client.qr_url(
            invoice_date=date(2026, 4, 6),
            seller_nip="1234567890",
            file_hash="abc123",
        )
        assert "qr-test.ksef.mf.gov.pl" in url
        assert "06-04-2026" in url
        assert "1234567890" in url
        assert "abc123" in url


# ---------------------------------------------------------------------------
# Sync KSeF wrapper
# ---------------------------------------------------------------------------


class TestSyncKSeF:
    def test_session_raises_not_implemented(self):
        from ksef import KSeF

        client = KSeF(nip="1234567890", token="tok", env="test")
        with pytest.raises(NotImplementedError, match="async"):
            client.session()
        client.close()

    def test_constructor_validates(self):
        from ksef import KSeF

        with pytest.raises(ValueError, match="nip is required"):
            KSeF(nip="", token="tok")
