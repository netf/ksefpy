from ksef.exceptions import (
    KSeFAuthError,
    KSeFCryptoError,
    KSeFError,
    KSeFInvoiceError,
    KSeFPermissionError,
    KSeFRateLimitError,
    KSeFServerError,
    KSeFSessionError,
    KSeFTimeoutError,
    KSeFXmlError,
    _ApiError,
)


def test_ksef_error_is_base():
    err = KSeFError("something broke")
    assert isinstance(err, Exception)
    assert "something broke" in str(err)


def test_ksef_error_carries_raw_response():
    err = KSeFError("bad", raw_response={"detail": "nope"})
    assert err.raw_response == {"detail": "nope"}
    assert "nope" in str(err)


def test_ksef_error_default_raw_response():
    err = KSeFError("simple")
    assert err.raw_response == {}


def test_auth_error():
    err = KSeFAuthError("not authed", raw_response={"title": "Unauthorized"})
    assert isinstance(err, KSeFError)
    assert err.raw_response["title"] == "Unauthorized"


def test_invoice_error():
    err = KSeFInvoiceError("bad invoice", raw_response={"code": "INVALID_INPUT"})
    assert isinstance(err, KSeFError)
    assert err.raw_response["code"] == "INVALID_INPUT"


def test_permission_error():
    err = KSeFPermissionError("no access", raw_response={"title": "Forbidden"})
    assert isinstance(err, KSeFError)


def test_rate_limit_error():
    err = KSeFRateLimitError(
        "too many requests",
        retry_after=30.0,
        raw_response={"error": "rate limited"},
    )
    assert isinstance(err, KSeFError)
    assert err.retry_after == 30.0
    assert "retry_after=30.0" in str(err)


def test_rate_limit_error_without_retry_after():
    err = KSeFRateLimitError("slow down")
    assert err.retry_after is None


def test_server_error():
    err = KSeFServerError("internal error", status_code=502)
    assert isinstance(err, KSeFError)
    assert err.status_code == 502


def test_session_error():
    err = KSeFSessionError("expired")
    assert isinstance(err, KSeFError)


def test_timeout_error():
    err = KSeFTimeoutError("polling timed out")
    assert isinstance(err, KSeFError)


def test_crypto_error():
    err = KSeFCryptoError("encryption failed")
    assert isinstance(err, KSeFError)


def test_xml_error_carries_validation_errors():
    err = KSeFXmlError("invalid xml", validation_errors=["missing field P_1", "invalid NIP"])
    assert len(err.validation_errors) == 2
    assert isinstance(err, KSeFError)


def test_internal_api_error():
    err = _ApiError("bad request", status_code=400, raw_response={"detail": "nope"})
    assert err.status_code == 400
    assert err.raw_response == {"detail": "nope"}
    assert not isinstance(err, KSeFError)  # _ApiError is internal, not public


def test_internal_api_error_retry_after():
    err = _ApiError("rate limited", status_code=429, retry_after=60.0)
    assert err.retry_after == 60.0
