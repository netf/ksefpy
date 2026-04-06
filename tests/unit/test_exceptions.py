from ksef.exceptions import (
    KSeFApiError,
    KSeFCryptoError,
    KSeFError,
    KSeFForbiddenError,
    KSeFRateLimitError,
    KSeFServerError,
    KSeFSessionError,
    KSeFTimeoutError,
    KSeFUnauthorizedError,
    KSeFXmlError,
)


def test_ksef_error_is_base():
    err = KSeFError("something broke")
    assert isinstance(err, Exception)
    assert str(err) == "something broke"


def test_api_error_carries_status_and_details():
    err = KSeFApiError(
        message="bad request",
        status_code=400,
        error_code="INVALID_INPUT",
        details=[{"field": "nip", "message": "invalid"}],
    )
    assert err.status_code == 400
    assert err.error_code == "INVALID_INPUT"
    assert err.details[0]["field"] == "nip"
    assert isinstance(err, KSeFError)


def test_unauthorized_error():
    err = KSeFUnauthorizedError(message="not authed", problem={"type": "about:blank", "title": "Unauthorized"})
    assert err.status_code == 401
    assert err.problem["title"] == "Unauthorized"


def test_forbidden_error():
    err = KSeFForbiddenError(message="no access", problem={"type": "about:blank", "title": "Forbidden"})
    assert err.status_code == 403


def test_rate_limit_error():
    err = KSeFRateLimitError(
        message="too many requests",
        retry_after=30.0,
        limit=100,
        remaining=0,
    )
    assert err.status_code == 429
    assert err.retry_after == 30.0
    assert err.limit == 100
    assert err.remaining == 0


def test_server_error():
    err = KSeFServerError(message="internal error", status_code=502)
    assert err.status_code == 502
    assert isinstance(err, KSeFApiError)


def test_crypto_error():
    err = KSeFCryptoError("encryption failed")
    assert isinstance(err, KSeFError)
    assert not isinstance(err, KSeFApiError)


def test_xml_error_carries_validation_errors():
    err = KSeFXmlError("invalid xml", validation_errors=["missing field P_1", "invalid NIP"])
    assert len(err.validation_errors) == 2
    assert isinstance(err, KSeFError)


def test_session_error():
    assert isinstance(KSeFSessionError("expired"), KSeFError)


def test_timeout_error():
    assert isinstance(KSeFTimeoutError("polling timed out"), KSeFError)
