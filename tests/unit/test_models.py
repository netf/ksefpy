from ksef.models.auth import (
    AuthenticationChallengeResponse,
    AuthenticationKsefTokenRequest,
    AuthenticationOperationStatusResponse,
    RefreshTokenResponse,
    SignatureResponse,
    TokenInfo,
)
from ksef.models.common import ContextIdentifier, ContextIdentifierType
from ksef.models.errors import ApiErrorResponse, ProblemDetails
from ksef.models.sessions import (
    EncryptionInfo,
    FileMetadata,
    FormCode,
    OpenOnlineSessionRequest,
    OpenOnlineSessionResponse,
    SendInvoiceRequest,
    SendInvoiceResponse,
    SessionStatusResponse,
)


def test_challenge_response_roundtrip():
    data = {
        "challenge": "abc123",
        "timestamp": "2026-04-06T10:00:00+00:00",
        "timestampMs": 1775386800000,
        "clientIp": "1.2.3.4",
    }
    resp = AuthenticationChallengeResponse.model_validate(data)
    assert resp.challenge == "abc123"
    assert resp.timestamp_ms == 1775386800000
    assert resp.client_ip == "1.2.3.4"


def test_context_identifier():
    ctx = ContextIdentifier(type=ContextIdentifierType.NIP, value="1234567890")
    assert ctx.type == ContextIdentifierType.NIP
    dumped = ctx.model_dump(by_alias=True)
    assert dumped["type"] == "nip"
    assert dumped["value"] == "1234567890"


def test_ksef_token_request():
    req = AuthenticationKsefTokenRequest(
        challenge="abc123",
        context_identifier=ContextIdentifier(type=ContextIdentifierType.NIP, value="1234567890"),
        encrypted_token="base64data==",
    )
    dumped = req.model_dump(by_alias=True)
    assert dumped["challenge"] == "abc123"
    assert dumped["encryptedToken"] == "base64data=="
    assert dumped["contextIdentifier"]["type"] == "nip"


def test_signature_response():
    data = {
        "referenceNumber": "ref-123",
        "authenticationToken": {"token": "temp-token", "validUntil": "2026-04-06T10:15:00+00:00"},
    }
    resp = SignatureResponse.model_validate(data)
    assert resp.reference_number == "ref-123"
    assert resp.authentication_token.token == "temp-token"


def test_token_info():
    data = {"token": "jwt-xyz", "validUntil": "2026-04-06T10:15:00+00:00"}
    info = TokenInfo.model_validate(data)
    assert info.token == "jwt-xyz"
    assert info.valid_until.year == 2026


def test_operation_status_response():
    data = {
        "accessToken": {"token": "access-jwt", "validUntil": "2026-04-06T10:15:00+00:00"},
        "refreshToken": {"token": "refresh-jwt", "validUntil": "2026-04-13T10:15:00+00:00"},
    }
    resp = AuthenticationOperationStatusResponse.model_validate(data)
    assert resp.access_token.token == "access-jwt"
    assert resp.refresh_token.token == "refresh-jwt"


def test_refresh_token_response():
    data = {"accessToken": {"token": "new-jwt", "validUntil": "2026-04-06T10:30:00+00:00"}}
    resp = RefreshTokenResponse.model_validate(data)
    assert resp.access_token.token == "new-jwt"


def test_form_code():
    fc = FormCode(system_code="FA (3)", schema_version="1-0E", value="FA")
    dumped = fc.model_dump(by_alias=True)
    assert dumped["systemCode"] == "FA (3)"


def test_encryption_info():
    info = EncryptionInfo(encrypted_symmetric_key="enc-key-base64", initialization_vector="iv-base64")
    dumped = info.model_dump(by_alias=True)
    assert dumped["encryptedSymmetricKey"] == "enc-key-base64"


def test_open_online_session_request():
    req = OpenOnlineSessionRequest(
        form_code=FormCode(system_code="FA (3)", schema_version="1-0E", value="FA"),
        encryption=EncryptionInfo(encrypted_symmetric_key="key", initialization_vector="iv"),
    )
    dumped = req.model_dump(by_alias=True)
    assert dumped["formCode"]["systemCode"] == "FA (3)"
    assert dumped["encryption"]["encryptedSymmetricKey"] == "key"


def test_open_online_session_response():
    data = {"referenceNumber": "sess-ref", "validUntil": "2026-04-07T10:00:00+00:00"}
    resp = OpenOnlineSessionResponse.model_validate(data)
    assert resp.reference_number == "sess-ref"


def test_send_invoice_request():
    req = SendInvoiceRequest(
        invoice_hash="sha256hex",
        invoice_size=1024,
        encrypted_invoice_hash="enc-sha256hex",
        encrypted_invoice_size=1040,
        encrypted_invoice_content="base64-encrypted-content",
        offline_mode=False,
    )
    dumped = req.model_dump(by_alias=True)
    assert dumped["invoiceHash"] == "sha256hex"
    assert dumped["encryptedInvoiceContent"] == "base64-encrypted-content"
    assert dumped["offlineMode"] is False


def test_send_invoice_response():
    data = {"referenceNumber": "inv-ref-123"}
    resp = SendInvoiceResponse.model_validate(data)
    assert resp.reference_number == "inv-ref-123"


def test_file_metadata():
    fm = FileMetadata(hash_sha="abcdef", file_size=2048)
    dumped = fm.model_dump(by_alias=True)
    assert dumped["hashSHA"] == "abcdef"


def test_api_error_response():
    data = {
        "exception": {
            "serviceCtx": "svc",
            "serviceCode": "20001",
            "serviceName": "validation",
            "timestamp": "2026-04-06T10:00:00+00:00",
            "referenceNumber": "ref",
            "exceptionDetailList": [{"exceptionCode": 123, "exceptionDescription": "Invalid NIP"}],
        }
    }
    resp = ApiErrorResponse.model_validate(data)
    assert resp.exception.service_code == "20001"
    assert resp.exception.exception_detail_list[0].exception_description == "Invalid NIP"


def test_problem_details():
    data = {"type": "about:blank", "title": "Unauthorized", "status": 401, "detail": "Token expired"}
    pd = ProblemDetails.model_validate(data)
    assert pd.title == "Unauthorized"
    assert pd.status == 401


def test_session_status_response():
    data = {
        "status": {"code": 200, "description": "OK"},
        "invoiceCount": 5,
        "successfulInvoiceCount": 4,
        "failedInvoiceCount": 1,
        "dateCreated": "2026-04-06T10:00:00+00:00",
        "dateUpdated": "2026-04-06T10:05:00+00:00",
    }
    resp = SessionStatusResponse.model_validate(data)
    assert resp.invoice_count == 5
    assert resp.failed_invoice_count == 1
