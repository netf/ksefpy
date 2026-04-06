# KSeF Python SDK Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modern Python SDK for the Polish KSeF e-Invoice API 2.0 with full endpoint coverage, crypto support, and high-level workflow coordinators.

**Architecture:** Hybrid approach — xsdata-generated invoice models from XSD schemas, hand-written Pydantic API models, httpx-based HTTP client. Two layers: low-level client (1:1 endpoints) + high-level coordinators (multi-step workflows). Async-first with sync wrappers.

**Tech Stack:** Python >=3.12, httpx, pydantic v2, xsdata, cryptography, signxml, qrcode/Pillow

**Spec:** `docs/superpowers/specs/2026-04-06-ksef-python-sdk-design.md`

---

## File Map

### Foundation (Tasks 1-3)
- Create: `ksef/__init__.py` — public API exports
- Create: `ksef/py.typed` — PEP 561 marker
- Create: `ksef/_version.py` — version string
- Create: `ksef/environments.py` — TEST, DEMO, PRODUCTION presets
- Create: `ksef/exceptions.py` — typed exception hierarchy
- Modify: `pyproject.toml` — dependencies, extras, package config

### Models (Task 4)
- Create: `ksef/models/__init__.py` — model exports
- Create: `ksef/models/common.py` — shared types (ContextIdentifier, pagination)
- Create: `ksef/models/errors.py` — ApiError, ProblemDetails
- Create: `ksef/models/auth.py` — auth request/response models
- Create: `ksef/models/sessions.py` — session models (encryption, forms, invoices)
- Create: `ksef/models/invoices.py` — invoice download/export models
- Create: `ksef/models/permissions.py` — permission grant/query models
- Create: `ksef/models/certificates.py` — certificate enrollment/query models
- Create: `ksef/models/tokens.py` — KSeF token models
- Create: `ksef/models/limits.py` — rate limit models

### Low-Level Client (Tasks 5-8)
- Create: `ksef/client/__init__.py` — client exports
- Create: `ksef/client/base.py` — BaseClient (httpx wrapper, error handling)
- Create: `ksef/client/auth.py` — AuthClient
- Create: `ksef/client/sessions.py` — ActiveSessionsClient
- Create: `ksef/client/online.py` — OnlineSessionClient
- Create: `ksef/client/batch.py` — BatchSessionClient
- Create: `ksef/client/session_status.py` — SessionStatusClient
- Create: `ksef/client/invoices.py` — InvoiceClient
- Create: `ksef/client/permissions.py` — PermissionClient
- Create: `ksef/client/certificates.py` — CertificateClient
- Create: `ksef/client/tokens.py` — KSeFTokenClient
- Create: `ksef/client/limits.py` — LimitsClient
- Create: `ksef/client/peppol.py` — PeppolClient
- Create: `ksef/client/testdata.py` — TestDataClient

### Crypto (Tasks 9-11)
- Create: `ksef/crypto/__init__.py` — crypto exports
- Create: `ksef/crypto/service.py` — CryptographyService
- Create: `ksef/crypto/xades.py` — XAdESService
- Create: `ksef/crypto/certificates.py` — CSR generation
- Create: `ksef/crypto/qr.py` — QR Code generation

### XML/Schemas (Task 12)
- Create: `ksef/xml.py` — serialize/deserialize/validate helpers
- Create: `ksef/schemas/__init__.py` — schema version enum
- Create: `ksef/schemas/fa_3/` — generated FA(3) dataclasses
- Create: `scripts/generate_schemas.sh` — XSD download + xsdata generation

### Coordinators (Tasks 13-16)
- Create: `ksef/coordinators/__init__.py` — coordinator exports
- Create: `ksef/coordinators/auth.py` — AuthCoordinator + AuthSession
- Create: `ksef/coordinators/online_session.py` — OnlineSessionManager
- Create: `ksef/coordinators/batch_session.py` — BatchSessionManager
- Create: `ksef/coordinators/invoice_download.py` — InvoiceDownloadManager

### Sync Wrappers (Task 17)
- Create: `ksef/_sync.py` — sync wrapper machinery
- Modify: `ksef/__init__.py` — add KSeFClient (sync) export

### Tests
- Create: `tests/__init__.py`
- Create: `tests/conftest.py` — shared fixtures, respx setup
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_environments.py`
- Create: `tests/unit/test_exceptions.py`
- Create: `tests/unit/test_models.py`
- Create: `tests/unit/test_base_client.py`
- Create: `tests/unit/test_auth_client.py`
- Create: `tests/unit/test_online_client.py`
- Create: `tests/unit/test_session_status_client.py`
- Create: `tests/unit/test_invoices_client.py`
- Create: `tests/unit/test_remaining_clients.py`
- Create: `tests/unit/test_crypto_service.py`
- Create: `tests/unit/test_xades.py`
- Create: `tests/unit/test_qr.py`
- Create: `tests/unit/test_xml.py`
- Create: `tests/unit/test_auth_coordinator.py`
- Create: `tests/unit/test_online_session_manager.py`
- Create: `tests/unit/test_batch_session_manager.py`
- Create: `tests/unit/test_invoice_download_manager.py`
- Create: `tests/unit/test_sync_client.py`

---

### Task 1: Project Setup & pyproject.toml

**Files:**
- Modify: `pyproject.toml`
- Create: `ksef/__init__.py`
- Create: `ksef/py.typed`
- Create: `ksef/_version.py`

- [ ] **Step 1: Update pyproject.toml with dependencies and package config**

```toml
[project]
name = "ksef"
version = "0.1.0"
description = "Modern Python SDK for the Polish KSeF e-Invoice API 2.0"
readme = "README.md"
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
    "xsdata>=24.0",
    "cryptography>=43.0",
]

[project.optional-dependencies]
xades = ["signxml>=4.0"]
qr = ["qrcode>=8.0", "Pillow>=11.0"]
all = ["ksef[xades,qr]"]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "respx>=0.22",
    "ruff>=0.8",
    "mypy>=1.13",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
```

- [ ] **Step 2: Create package init files**

`ksef/_version.py`:
```python
__version__ = "0.1.0"
```

`ksef/py.typed` — empty file (PEP 561 marker).

`ksef/__init__.py`:
```python
from ksef._version import __version__
from ksef.environments import Environment

__all__ = ["__version__", "Environment"]
```

- [ ] **Step 3: Install dependencies**

Run: `uv sync`
Expected: dependencies install successfully.

- [ ] **Step 4: Verify import works**

Run: `uv run python -c "import ksef; print(ksef.__version__)"`
Expected: `0.1.0`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml ksef/__init__.py ksef/_version.py ksef/py.typed uv.lock
git commit -m "feat: project setup with dependencies and package config"
```

---

### Task 2: Environments

**Files:**
- Create: `ksef/environments.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_environments.py`

- [ ] **Step 1: Write failing test for Environment**

`tests/__init__.py` — empty file.
`tests/unit/__init__.py` — empty file.

`tests/conftest.py`:
```python
"""Shared test fixtures."""
```

`tests/unit/test_environments.py`:
```python
from ksef.environments import Environment


def test_test_environment_has_correct_api_url():
    assert Environment.TEST.api_base_url == "https://api-test.ksef.mf.gov.pl/v2"


def test_demo_environment_has_correct_api_url():
    assert Environment.DEMO.api_base_url == "https://api-demo.ksef.mf.gov.pl/v2"


def test_production_environment_has_correct_api_url():
    assert Environment.PRODUCTION.api_base_url == "https://api.ksef.mf.gov.pl/v2"


def test_environment_is_frozen():
    env = Environment.TEST
    try:
        env.api_base_url = "https://changed.example.com"  # type: ignore[misc]
        assert False, "Should have raised"
    except AttributeError:
        pass


def test_test_environment_qr_url():
    assert Environment.TEST.qr_base_url == "https://qr-test.ksef.mf.gov.pl"


def test_production_qr_url():
    assert Environment.PRODUCTION.qr_base_url == "https://qr.ksef.mf.gov.pl"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_environments.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ksef.environments'`

- [ ] **Step 3: Implement Environment**

`ksef/environments.py`:
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Environment:
    """KSeF API environment configuration."""

    name: str
    api_base_url: str
    qr_base_url: str


Environment.TEST = Environment(  # type: ignore[attr-defined]
    name="TEST",
    api_base_url="https://api-test.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr-test.ksef.mf.gov.pl",
)

Environment.DEMO = Environment(  # type: ignore[attr-defined]
    name="DEMO",
    api_base_url="https://api-demo.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr-demo.ksef.mf.gov.pl",
)

Environment.PRODUCTION = Environment(  # type: ignore[attr-defined]
    name="PRODUCTION",
    api_base_url="https://api.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr.ksef.mf.gov.pl",
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_environments.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add ksef/environments.py tests/
git commit -m "feat: add Environment dataclass with TEST, DEMO, PRODUCTION presets"
```

---

### Task 3: Exceptions

**Files:**
- Create: `ksef/exceptions.py`
- Create: `tests/unit/test_exceptions.py`

- [ ] **Step 1: Write failing tests for exceptions**

`tests/unit/test_exceptions.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_exceptions.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement exceptions**

`ksef/exceptions.py`:
```python
from __future__ import annotations

from typing import Any


class KSeFError(Exception):
    """Base exception for all KSeF SDK errors."""


class KSeFApiError(KSeFError):
    """API returned an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []


class KSeFUnauthorizedError(KSeFApiError):
    """HTTP 401 — authentication failed. Carries RFC 7807 ProblemDetails."""

    def __init__(self, message: str, problem: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=401)
        self.problem = problem or {}


class KSeFForbiddenError(KSeFApiError):
    """HTTP 403 — insufficient permissions. Carries RFC 7807 ProblemDetails."""

    def __init__(self, message: str, problem: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=403)
        self.problem = problem or {}


class KSeFRateLimitError(KSeFApiError):
    """HTTP 429 — rate limited."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        limit: int | None = None,
        remaining: int | None = None,
    ) -> None:
        super().__init__(message=message, status_code=429)
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining


class KSeFServerError(KSeFApiError):
    """HTTP 5xx — server-side error."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message=message, status_code=status_code)


class KSeFCryptoError(KSeFError):
    """Encryption, signing, or key management failure."""


class KSeFXmlError(KSeFError):
    """XML serialization, deserialization, or validation failure."""

    def __init__(self, message: str, validation_errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.validation_errors = validation_errors or []


class KSeFSessionError(KSeFError):
    """Session lifecycle error (expired, already closed, etc.)."""


class KSeFTimeoutError(KSeFError):
    """Polling timeout (UPO retrieval, auth status, export)."""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_exceptions.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add ksef/exceptions.py tests/unit/test_exceptions.py
git commit -m "feat: add typed exception hierarchy"
```

---

### Task 4: Pydantic Models

**Files:**
- Create: `ksef/models/__init__.py`
- Create: `ksef/models/common.py`
- Create: `ksef/models/errors.py`
- Create: `ksef/models/auth.py`
- Create: `ksef/models/sessions.py`
- Create: `ksef/models/invoices.py`
- Create: `ksef/models/permissions.py`
- Create: `ksef/models/certificates.py`
- Create: `ksef/models/tokens.py`
- Create: `ksef/models/limits.py`
- Create: `tests/unit/test_models.py`

- [ ] **Step 1: Write failing tests for core models**

`tests/unit/test_models.py`:
```python
from datetime import datetime, timezone

from ksef.models.auth import (
    AuthenticationChallengeResponse,
    AuthenticationKsefTokenRequest,
    AuthenticationOperationStatusResponse,
    RefreshTokenResponse,
    SignatureResponse,
    TokenInfo,
)
from ksef.models.common import ContextIdentifier, ContextIdentifierType
from ksef.models.sessions import (
    EncryptionData,
    EncryptionInfo,
    FileMetadata,
    FormCode,
    OpenOnlineSessionRequest,
    OpenOnlineSessionResponse,
    SendInvoiceRequest,
    SendInvoiceResponse,
    SessionStatusResponse,
)
from ksef.models.errors import ApiErrorResponse, ProblemDetails


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
    fc = FormCode(system_code="FA (3)", schema_version="FA_2025010901", value="FA")
    dumped = fc.model_dump(by_alias=True)
    assert dumped["systemCode"] == "FA (3)"


def test_encryption_info():
    info = EncryptionInfo(encrypted_symmetric_key="enc-key-base64", initialization_vector="iv-base64")
    dumped = info.model_dump(by_alias=True)
    assert dumped["encryptedSymmetricKey"] == "enc-key-base64"


def test_open_online_session_request():
    req = OpenOnlineSessionRequest(
        form_code=FormCode(system_code="FA (3)", schema_version="FA_2025010901", value="FA"),
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
            "exceptionDetailList": [
                {"exceptionCode": 123, "exceptionDescription": "Invalid NIP"}
            ],
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
        "status": {"code": "200", "description": "OK"},
        "invoiceCount": 5,
        "successfulInvoiceCount": 4,
        "failedInvoiceCount": 1,
        "dateCreated": "2026-04-06T10:00:00+00:00",
        "dateUpdated": "2026-04-06T10:05:00+00:00",
    }
    resp = SessionStatusResponse.model_validate(data)
    assert resp.invoice_count == 5
    assert resp.failed_invoice_count == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement models**

`ksef/models/__init__.py`:
```python
"""Pydantic models for KSeF API requests and responses."""
```

`ksef/models/common.py`:
```python
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class KSeFModel(BaseModel):
    """Base model with camelCase alias generation."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda field_name: "".join(
            word.capitalize() if i > 0 else word for i, word in enumerate(field_name.split("_"))
        ),
    )


class ContextIdentifierType(StrEnum):
    NIP = "nip"
    INTERNAL_ID = "onip"
    EU_VAT = "nipVatUe"


class ContextIdentifier(KSeFModel):
    type: ContextIdentifierType
    value: str


class OperationStatusInfo(KSeFModel):
    code: str
    description: str | None = None


class PaginationParams(KSeFModel):
    page: int = 0
    page_size: int = 10
```

`ksef/models/errors.py`:
```python
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
```

`ksef/models/auth.py`:
```python
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
```

`ksef/models/sessions.py`:
```python
from __future__ import annotations

from datetime import datetime

from ksef.models.common import KSeFModel, OperationStatusInfo


class FormCode(KSeFModel):
    system_code: str
    schema_version: str
    value: str


class EncryptionInfo(KSeFModel):
    encrypted_symmetric_key: str
    initialization_vector: str


class EncryptionData(KSeFModel):
    cipher_key: bytes
    cipher_iv: bytes
    encryption_info: EncryptionInfo


class FileMetadata(KSeFModel):
    hash_sha: str
    file_size: int


class OpenOnlineSessionRequest(KSeFModel):
    form_code: FormCode
    encryption: EncryptionInfo


class OpenOnlineSessionResponse(KSeFModel):
    reference_number: str
    valid_until: datetime


class SendInvoiceRequest(KSeFModel):
    invoice_hash: str
    invoice_size: int
    encrypted_invoice_hash: str
    encrypted_invoice_size: int
    encrypted_invoice_content: str
    offline_mode: bool = False
    hash_of_corrected_invoice: str | None = None


class SendInvoiceResponse(KSeFModel):
    reference_number: str


class SessionStatusResponse(KSeFModel):
    status: OperationStatusInfo | None = None
    upo: dict | None = None
    invoice_count: int | None = None
    successful_invoice_count: int | None = None
    failed_invoice_count: int | None = None
    valid_until: datetime | None = None
    date_created: datetime | None = None
    date_updated: datetime | None = None
```

`ksef/models/invoices.py`:
```python
from __future__ import annotations

from datetime import datetime

from ksef.models.common import KSeFModel, OperationStatusInfo


class InvoiceMetadataQuery(KSeFModel):
    date_from: datetime
    date_to: datetime
    nip_sender: str | None = None
    nip_recipient: str | None = None
    page: int = 0
    page_size: int = 10


class InvoiceMetadata(KSeFModel):
    ksef_number: str
    subject_nip: str | None = None
    invoice_date: datetime | None = None
    net_amount: str | None = None
    vat_amount: str | None = None
    gross_amount: str | None = None


class InvoiceMetadataResponse(KSeFModel):
    items: list[InvoiceMetadata] = []
    continuation_token: str | None = None


class ExportRequest(KSeFModel):
    date_from: datetime
    date_to: datetime
    only_metadata: bool = False


class ExportStatusResponse(KSeFModel):
    status: OperationStatusInfo
    reference_number: str | None = None
```

`ksef/models/permissions.py`:
```python
from __future__ import annotations

from ksef.models.common import ContextIdentifier, KSeFModel, OperationStatusInfo


class PersonPermissionGrantRequest(KSeFModel):
    subject_identifier: ContextIdentifier
    permissions: list[str]
    subject_details: dict | None = None


class EntityPermissionGrantRequest(KSeFModel):
    subject_identifier: ContextIdentifier
    permissions: list[str]
    can_delegate: bool = False
    subject_details: dict | None = None


class PermissionOperationStatusResponse(KSeFModel):
    status: OperationStatusInfo
    reference_number: str | None = None


class PermissionQueryRequest(KSeFModel):
    page: int = 0
    page_size: int = 10


class PermissionGrantResponse(KSeFModel):
    reference_number: str
```

`ksef/models/certificates.py`:
```python
from __future__ import annotations

from datetime import datetime

from ksef.models.common import KSeFModel


class CertificateLimitResponse(KSeFModel):
    limit: int
    active_count: int
    can_enroll: bool


class CertificateEnrollmentDataResponse(KSeFModel):
    distinguished_name: dict


class CertificateEnrollRequest(KSeFModel):
    name: str
    certificate_type: str
    csr: str
    valid_from: datetime | None = None


class CertificateEnrollResponse(KSeFModel):
    reference_number: str


class CertificateEnrollmentStatusResponse(KSeFModel):
    status: str
    certificate_serial_number: str | None = None


class CertificateRetrieveRequest(KSeFModel):
    serial_numbers: list[str]


class CertificateInfo(KSeFModel):
    certificate: str
    serial_number: str | None = None
    name: str | None = None
    certificate_type: str | None = None
    status: str | None = None


class CertificateQueryRequest(KSeFModel):
    status: str | None = None
    name: str | None = None
    certificate_type: str | None = None
    page: int = 0
    page_size: int = 10


class CertificateQueryResponse(KSeFModel):
    items: list[CertificateInfo] = []
    continuation_token: str | None = None
```

`ksef/models/tokens.py`:
```python
from __future__ import annotations

from datetime import datetime

from ksef.models.common import ContextIdentifier, KSeFModel


class KSeFTokenGenerateRequest(KSeFModel):
    context_identifier: ContextIdentifier
    permissions: list[str]
    description: str | None = None


class KSeFTokenResponse(KSeFModel):
    reference_number: str


class KSeFTokenInfo(KSeFModel):
    reference_number: str
    description: str | None = None
    status: str | None = None
    permissions: list[str] = []
    date_created: datetime | None = None


class KSeFTokenListResponse(KSeFModel):
    items: list[KSeFTokenInfo] = []
    continuation_token: str | None = None
```

`ksef/models/limits.py`:
```python
from __future__ import annotations

from ksef.models.common import KSeFModel


class ContextLimits(KSeFModel):
    max_online_sessions: int | None = None
    max_batch_sessions: int | None = None
    active_online_sessions: int | None = None
    active_batch_sessions: int | None = None


class SubjectLimits(KSeFModel):
    max_certificates: int | None = None
    active_certificates: int | None = None


class RateLimitEntry(KSeFModel):
    group: str | None = None
    per_second: int | None = None
    per_minute: int | None = None
    per_hour: int | None = None


class RateLimitsResponse(KSeFModel):
    limits: list[RateLimitEntry] = []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_models.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add ksef/models/ tests/unit/test_models.py
git commit -m "feat: add Pydantic models for API requests and responses"
```

---

### Task 5: Base Client

**Files:**
- Create: `ksef/client/__init__.py`
- Create: `ksef/client/base.py`
- Create: `tests/unit/test_base_client.py`

- [ ] **Step 1: Write failing tests for BaseClient**

`tests/unit/test_base_client.py`:
```python
import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.environments import Environment
from ksef.exceptions import (
    KSeFApiError,
    KSeFForbiddenError,
    KSeFRateLimitError,
    KSeFServerError,
    KSeFUnauthorizedError,
)


@pytest.fixture
def base_client():
    client = BaseClient(environment=Environment.TEST)
    yield client


@respx.mock
@pytest.mark.asyncio
async def test_get_request(base_client: BaseClient):
    route = respx.get("https://api-test.ksef.mf.gov.pl/v2/auth/sessions").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    resp = await base_client.get("auth/sessions", access_token="tok")
    assert resp == {"items": []}
    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_post_request(base_client: BaseClient):
    route = respx.post("https://api-test.ksef.mf.gov.pl/v2/auth/challenge").mock(
        return_value=httpx.Response(200, json={"challenge": "xyz"})
    )
    resp = await base_client.post("auth/challenge")
    assert resp == {"challenge": "xyz"}


@respx.mock
@pytest.mark.asyncio
async def test_auth_header_included(base_client: BaseClient):
    route = respx.get("https://api-test.ksef.mf.gov.pl/v2/some/path").mock(
        return_value=httpx.Response(200, json={})
    )
    await base_client.get("some/path", access_token="my-jwt")
    assert route.calls[0].request.headers["Authorization"] == "Bearer my-jwt"


@respx.mock
@pytest.mark.asyncio
async def test_400_raises_api_error(base_client: BaseClient):
    respx.post("https://api-test.ksef.mf.gov.pl/v2/bad").mock(
        return_value=httpx.Response(
            400,
            json={"exception": {"serviceCode": "20001", "exceptionDetailList": []}},
        )
    )
    with pytest.raises(KSeFApiError) as exc_info:
        await base_client.post("bad")
    assert exc_info.value.status_code == 400


@respx.mock
@pytest.mark.asyncio
async def test_401_raises_unauthorized(base_client: BaseClient):
    respx.get("https://api-test.ksef.mf.gov.pl/v2/auth").mock(
        return_value=httpx.Response(401, json={"type": "about:blank", "title": "Unauthorized"})
    )
    with pytest.raises(KSeFUnauthorizedError):
        await base_client.get("auth")


@respx.mock
@pytest.mark.asyncio
async def test_403_raises_forbidden(base_client: BaseClient):
    respx.get("https://api-test.ksef.mf.gov.pl/v2/perm").mock(
        return_value=httpx.Response(403, json={"type": "about:blank", "title": "Forbidden"})
    )
    with pytest.raises(KSeFForbiddenError):
        await base_client.get("perm")


@respx.mock
@pytest.mark.asyncio
async def test_429_raises_rate_limit(base_client: BaseClient):
    respx.post("https://api-test.ksef.mf.gov.pl/v2/invoke").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "30"}, json={})
    )
    with pytest.raises(KSeFRateLimitError) as exc_info:
        await base_client.post("invoke")
    assert exc_info.value.retry_after == 30.0


@respx.mock
@pytest.mark.asyncio
async def test_500_raises_server_error(base_client: BaseClient):
    respx.get("https://api-test.ksef.mf.gov.pl/v2/down").mock(
        return_value=httpx.Response(502, text="Bad Gateway")
    )
    with pytest.raises(KSeFServerError) as exc_info:
        await base_client.get("down")
    assert exc_info.value.status_code == 502


@respx.mock
@pytest.mark.asyncio
async def test_delete_request(base_client: BaseClient):
    route = respx.delete("https://api-test.ksef.mf.gov.pl/v2/tokens/ref-1").mock(
        return_value=httpx.Response(204)
    )
    resp = await base_client.delete("tokens/ref-1", access_token="tok")
    assert resp is None
    assert route.called
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_base_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement BaseClient**

`ksef/client/__init__.py`:
```python
"""Low-level KSeF API client modules."""
```

`ksef/client/base.py`:
```python
from __future__ import annotations

import logging
from typing import Any

import httpx

from ksef.environments import Environment
from ksef.exceptions import (
    KSeFApiError,
    KSeFForbiddenError,
    KSeFRateLimitError,
    KSeFServerError,
    KSeFUnauthorizedError,
)

logger = logging.getLogger("ksef")


class BaseClient:
    """Low-level HTTP wrapper for the KSeF API."""

    def __init__(
        self,
        environment: Environment,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.environment = environment
        self._base_url = environment.api_base_url.rstrip("/")
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def __aenter__(self) -> BaseClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _headers(self, access_token: str | None = None) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def _handle_response(self, response: httpx.Response) -> Any:
        status = response.status_code
        logger.debug("HTTP %s %s -> %d", response.request.method, response.request.url, status)

        if status == 204:
            return None

        if 200 <= status < 300:
            return response.json()

        body: dict[str, Any] = {}
        try:
            body = response.json()
        except Exception:
            pass

        if status == 401:
            raise KSeFUnauthorizedError(
                message=body.get("title", "Unauthorized"),
                problem=body,
            )
        if status == 403:
            raise KSeFForbiddenError(
                message=body.get("title", "Forbidden"),
                problem=body,
            )
        if status == 429:
            retry_after: float | None = None
            raw = response.headers.get("Retry-After")
            if raw:
                try:
                    retry_after = float(raw)
                except ValueError:
                    pass
            raise KSeFRateLimitError(
                message="Rate limited",
                retry_after=retry_after,
            )
        if status >= 500:
            raise KSeFServerError(
                message=body.get("title", response.text[:200] if response.text else "Server error"),
                status_code=status,
            )

        error_code: str | None = None
        details: list[dict[str, Any]] = []
        if "exception" in body:
            exc_content = body["exception"]
            error_code = exc_content.get("serviceCode")
            details = exc_content.get("exceptionDetailList", [])

        raise KSeFApiError(
            message=f"API error {status}",
            status_code=status,
            error_code=error_code,
            details=details,
        )

    async def get(self, path: str, *, access_token: str | None = None, params: dict[str, Any] | None = None) -> Any:
        response = await self._http.get(self._url(path), headers=self._headers(access_token), params=params)
        return await self._handle_response(response)

    async def post(
        self,
        path: str,
        *,
        access_token: str | None = None,
        json: Any = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        h = self._headers(access_token)
        if headers:
            h.update(headers)
        response = await self._http.post(self._url(path), headers=h, json=json, content=content)
        return await self._handle_response(response)

    async def put(
        self,
        path: str,
        *,
        access_token: str | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        h = self._headers(access_token)
        if headers:
            h.update(headers)
        response = await self._http.put(self._url(path), headers=h, content=content)
        return await self._handle_response(response)

    async def delete(self, path: str, *, access_token: str | None = None) -> Any:
        response = await self._http.delete(self._url(path), headers=self._headers(access_token))
        return await self._handle_response(response)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_base_client.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add ksef/client/ tests/unit/test_base_client.py
git commit -m "feat: add BaseClient with httpx, error handling, and auth headers"
```

---

### Task 6: Auth Client

**Files:**
- Create: `ksef/client/auth.py`
- Create: `tests/unit/test_auth_client.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_auth_client.py`:
```python
import httpx
import pytest
import respx

from ksef.client.auth import AuthClient
from ksef.client.base import BaseClient
from ksef.environments import Environment
from ksef.models.auth import (
    AuthenticationChallengeResponse,
    AuthenticationKsefTokenRequest,
    AuthenticationOperationStatusResponse,
    RefreshTokenResponse,
    SignatureResponse,
)
from ksef.models.common import ContextIdentifier, ContextIdentifierType

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def auth_client():
    base = BaseClient(environment=Environment.TEST)
    return AuthClient(base)


@respx.mock
@pytest.mark.asyncio
async def test_get_challenge(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/challenge").mock(
        return_value=httpx.Response(200, json={
            "challenge": "abc123",
            "timestamp": "2026-04-06T10:00:00+00:00",
            "timestampMs": 1775386800000,
            "clientIp": "1.2.3.4",
        })
    )
    result = await auth_client.get_challenge()
    assert isinstance(result, AuthenticationChallengeResponse)
    assert result.challenge == "abc123"


@respx.mock
@pytest.mark.asyncio
async def test_submit_ksef_token(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/ksef-token").mock(
        return_value=httpx.Response(200, json={
            "referenceNumber": "ref-1",
            "authenticationToken": {"token": "temp-tok", "validUntil": "2026-04-06T11:00:00+00:00"},
        })
    )
    req = AuthenticationKsefTokenRequest(
        challenge="abc",
        context_identifier=ContextIdentifier(type=ContextIdentifierType.NIP, value="1234567890"),
        encrypted_token="enc-data",
    )
    result = await auth_client.submit_ksef_token(req)
    assert isinstance(result, SignatureResponse)
    assert result.reference_number == "ref-1"


@respx.mock
@pytest.mark.asyncio
async def test_submit_xades_signature(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/xades-signature").mock(
        return_value=httpx.Response(200, json={
            "referenceNumber": "ref-2",
            "authenticationToken": {"token": "temp-tok-2", "validUntil": "2026-04-06T11:00:00+00:00"},
        })
    )
    result = await auth_client.submit_xades_signature("<xml/>", access_token="tok")
    assert isinstance(result, SignatureResponse)
    assert result.reference_number == "ref-2"


@respx.mock
@pytest.mark.asyncio
async def test_redeem_token(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/token/redeem").mock(
        return_value=httpx.Response(200, json={
            "accessToken": {"token": "access-jwt", "validUntil": "2026-04-06T10:15:00+00:00"},
            "refreshToken": {"token": "refresh-jwt", "validUntil": "2026-04-13T10:15:00+00:00"},
        })
    )
    result = await auth_client.redeem_token(authentication_token="temp-tok")
    assert isinstance(result, AuthenticationOperationStatusResponse)
    assert result.access_token.token == "access-jwt"


@respx.mock
@pytest.mark.asyncio
async def test_refresh_token(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/token/refresh").mock(
        return_value=httpx.Response(200, json={
            "accessToken": {"token": "new-jwt", "validUntil": "2026-04-06T10:30:00+00:00"},
        })
    )
    result = await auth_client.refresh_token(refresh_token="refresh-jwt")
    assert isinstance(result, RefreshTokenResponse)
    assert result.access_token.token == "new-jwt"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_auth_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement AuthClient**

`ksef/client/auth.py`:
```python
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
        extra_headers: dict[str, str] = {}
        if enforce_xades_compliance:
            extra_headers["X-KSeF-Feature"] = "enforce-xades-compliance"
        data = await self._base.post(
            "auth/xades-signature",
            access_token=access_token,
            content=signed_xml.encode("utf-8"),
            headers={"Content-Type": "application/xml", **extra_headers},
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_auth_client.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add ksef/client/auth.py tests/unit/test_auth_client.py
git commit -m "feat: add AuthClient with challenge, token, xades, redeem, refresh"
```

---

### Task 7: Online Session & Session Status Clients

**Files:**
- Create: `ksef/client/online.py`
- Create: `ksef/client/session_status.py`
- Create: `tests/unit/test_online_client.py`
- Create: `tests/unit/test_session_status_client.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_online_client.py`:
```python
import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.client.online import OnlineSessionClient
from ksef.environments import Environment
from ksef.models.sessions import (
    EncryptionInfo,
    FormCode,
    OpenOnlineSessionRequest,
    OpenOnlineSessionResponse,
    SendInvoiceRequest,
    SendInvoiceResponse,
)

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def online_client():
    return OnlineSessionClient(BaseClient(environment=Environment.TEST))


@respx.mock
@pytest.mark.asyncio
async def test_open_online_session(online_client: OnlineSessionClient):
    respx.post(f"{BASE}/sessions/online").mock(
        return_value=httpx.Response(201, json={
            "referenceNumber": "sess-1",
            "validUntil": "2026-04-06T22:00:00+00:00",
        })
    )
    req = OpenOnlineSessionRequest(
        form_code=FormCode(system_code="FA (3)", schema_version="FA_2025010901", value="FA"),
        encryption=EncryptionInfo(encrypted_symmetric_key="key", initialization_vector="iv"),
    )
    result = await online_client.open(req, access_token="tok")
    assert isinstance(result, OpenOnlineSessionResponse)
    assert result.reference_number == "sess-1"


@respx.mock
@pytest.mark.asyncio
async def test_send_invoice(online_client: OnlineSessionClient):
    respx.post(f"{BASE}/sessions/online/sess-1/invoices").mock(
        return_value=httpx.Response(201, json={"referenceNumber": "inv-1"})
    )
    req = SendInvoiceRequest(
        invoice_hash="hash1", invoice_size=100,
        encrypted_invoice_hash="enchash1", encrypted_invoice_size=120,
        encrypted_invoice_content="base64data",
    )
    result = await online_client.send_invoice(req, "sess-1", access_token="tok")
    assert isinstance(result, SendInvoiceResponse)
    assert result.reference_number == "inv-1"


@respx.mock
@pytest.mark.asyncio
async def test_close_session(online_client: OnlineSessionClient):
    respx.post(f"{BASE}/sessions/online/sess-1/close").mock(
        return_value=httpx.Response(200, json={})
    )
    await online_client.close("sess-1", access_token="tok")
```

`tests/unit/test_session_status_client.py`:
```python
import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.client.session_status import SessionStatusClient
from ksef.environments import Environment
from ksef.models.sessions import SessionStatusResponse

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def status_client():
    return SessionStatusClient(BaseClient(environment=Environment.TEST))


@respx.mock
@pytest.mark.asyncio
async def test_get_session_status(status_client: SessionStatusClient):
    respx.get(f"{BASE}/sessions/sess-1").mock(
        return_value=httpx.Response(200, json={
            "status": {"code": "200", "description": "OK"},
            "invoiceCount": 3,
            "successfulInvoiceCount": 2,
            "failedInvoiceCount": 1,
            "dateCreated": "2026-04-06T10:00:00+00:00",
            "dateUpdated": "2026-04-06T10:05:00+00:00",
        })
    )
    result = await status_client.get_session_status("sess-1", access_token="tok")
    assert isinstance(result, SessionStatusResponse)
    assert result.invoice_count == 3


@respx.mock
@pytest.mark.asyncio
async def test_get_session_invoices(status_client: SessionStatusClient):
    respx.get(f"{BASE}/sessions/sess-1/invoices").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    result = await status_client.get_session_invoices("sess-1", access_token="tok")
    assert result == {"items": []}


@respx.mock
@pytest.mark.asyncio
async def test_get_upo(status_client: SessionStatusClient):
    respx.get(f"{BASE}/sessions/sess-1/upo/upo-ref").mock(
        return_value=httpx.Response(200, json={"upo": "data"})
    )
    result = await status_client.get_upo("sess-1", "upo-ref", access_token="tok")
    assert result == {"upo": "data"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_online_client.py tests/unit/test_session_status_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement OnlineSessionClient**

`ksef/client/online.py`:
```python
from __future__ import annotations

from ksef.client.base import BaseClient
from ksef.models.sessions import (
    OpenOnlineSessionRequest,
    OpenOnlineSessionResponse,
    SendInvoiceRequest,
    SendInvoiceResponse,
)


class OnlineSessionClient:
    """Client for KSeF interactive (online) session endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def open(
        self,
        request: OpenOnlineSessionRequest,
        *,
        access_token: str,
        upo_version: str | None = None,
    ) -> OpenOnlineSessionResponse:
        """POST /sessions/online"""
        headers: dict[str, str] = {}
        if upo_version:
            headers["X-KSeF-Feature"] = f"upo-version:{upo_version}"
        data = await self._base.post(
            "sessions/online",
            access_token=access_token,
            json=request.model_dump(by_alias=True, exclude_none=True),
            headers=headers or None,
        )
        return OpenOnlineSessionResponse.model_validate(data)

    async def send_invoice(
        self,
        request: SendInvoiceRequest,
        session_reference_number: str,
        *,
        access_token: str,
    ) -> SendInvoiceResponse:
        """POST /sessions/online/{ref}/invoices"""
        data = await self._base.post(
            f"sessions/online/{session_reference_number}/invoices",
            access_token=access_token,
            json=request.model_dump(by_alias=True, exclude_none=True),
        )
        return SendInvoiceResponse.model_validate(data)

    async def close(self, session_reference_number: str, *, access_token: str) -> None:
        """POST /sessions/online/{ref}/close"""
        await self._base.post(
            f"sessions/online/{session_reference_number}/close",
            access_token=access_token,
        )
```

- [ ] **Step 4: Implement SessionStatusClient**

`ksef/client/session_status.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient
from ksef.models.sessions import SessionStatusResponse


class SessionStatusClient:
    """Client for session status, invoice status, and UPO endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def get_session_status(self, reference_number: str, *, access_token: str) -> SessionStatusResponse:
        """GET /sessions/{ref}"""
        data = await self._base.get(f"sessions/{reference_number}", access_token=access_token)
        return SessionStatusResponse.model_validate(data)

    async def get_session_invoices(
        self, reference_number: str, *, access_token: str, params: dict[str, Any] | None = None
    ) -> dict:
        """GET /sessions/{ref}/invoices"""
        return await self._base.get(f"sessions/{reference_number}/invoices", access_token=access_token, params=params)

    async def get_failed_invoices(
        self, reference_number: str, *, access_token: str, params: dict[str, Any] | None = None
    ) -> dict:
        """GET /sessions/{ref}/invoices/failed"""
        return await self._base.get(
            f"sessions/{reference_number}/invoices/failed", access_token=access_token, params=params
        )

    async def get_invoice_status(
        self, session_ref: str, invoice_ref: str, *, access_token: str
    ) -> dict:
        """GET /sessions/{ref}/invoices/{invoiceRef}"""
        return await self._base.get(
            f"sessions/{session_ref}/invoices/{invoice_ref}", access_token=access_token
        )

    async def get_upo(self, session_ref: str, upo_ref: str, *, access_token: str) -> dict:
        """GET /sessions/{ref}/upo/{upoRef}"""
        return await self._base.get(f"sessions/{session_ref}/upo/{upo_ref}", access_token=access_token)

    async def get_upo_by_ksef_number(
        self, session_ref: str, ksef_number: str, *, access_token: str
    ) -> dict:
        """GET /sessions/{ref}/invoices/ksef/{ksefNumber}/upo"""
        return await self._base.get(
            f"sessions/{session_ref}/invoices/ksef/{ksef_number}/upo", access_token=access_token
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_online_client.py tests/unit/test_session_status_client.py -v`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add ksef/client/online.py ksef/client/session_status.py tests/unit/test_online_client.py tests/unit/test_session_status_client.py
git commit -m "feat: add OnlineSessionClient and SessionStatusClient"
```

---

### Task 8: Remaining Low-Level Clients

**Files:**
- Create: `ksef/client/batch.py`
- Create: `ksef/client/invoices.py`
- Create: `ksef/client/sessions.py`
- Create: `ksef/client/permissions.py`
- Create: `ksef/client/certificates.py`
- Create: `ksef/client/tokens.py`
- Create: `ksef/client/limits.py`
- Create: `ksef/client/peppol.py`
- Create: `ksef/client/testdata.py`
- Create: `tests/unit/test_invoices_client.py`
- Create: `tests/unit/test_remaining_clients.py`

- [ ] **Step 1: Write failing tests for InvoiceClient**

`tests/unit/test_invoices_client.py`:
```python
import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.client.invoices import InvoiceClient
from ksef.environments import Environment

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def invoice_client():
    return InvoiceClient(BaseClient(environment=Environment.TEST))


@respx.mock
@pytest.mark.asyncio
async def test_download_invoice(invoice_client: InvoiceClient):
    respx.get(f"{BASE}/invoices/ksef/KSEF-123").mock(
        return_value=httpx.Response(200, content=b"<xml>invoice</xml>", headers={"Content-Type": "application/xml"})
    )
    result = await invoice_client.download("KSEF-123", access_token="tok")
    assert result == b"<xml>invoice</xml>"


@respx.mock
@pytest.mark.asyncio
async def test_query_metadata(invoice_client: InvoiceClient):
    respx.post(f"{BASE}/invoices/query/metadata").mock(
        return_value=httpx.Response(200, json={"items": [], "continuationToken": None})
    )
    result = await invoice_client.query_metadata(
        {"dateFrom": "2026-01-01", "dateTo": "2026-03-31"},
        access_token="tok",
    )
    assert result["items"] == []


@respx.mock
@pytest.mark.asyncio
async def test_export(invoice_client: InvoiceClient):
    respx.post(f"{BASE}/invoices/exports").mock(
        return_value=httpx.Response(200, json={"referenceNumber": "exp-1"})
    )
    result = await invoice_client.export(
        {"dateFrom": "2026-01-01", "dateTo": "2026-03-31"},
        access_token="tok",
    )
    assert result["referenceNumber"] == "exp-1"


@respx.mock
@pytest.mark.asyncio
async def test_get_export_status(invoice_client: InvoiceClient):
    respx.get(f"{BASE}/invoices/exports/exp-1").mock(
        return_value=httpx.Response(200, json={"status": {"code": "200"}})
    )
    result = await invoice_client.get_export_status("exp-1", access_token="tok")
    assert result["status"]["code"] == "200"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_invoices_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement InvoiceClient**

`ksef/client/invoices.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class InvoiceClient:
    """Client for invoice download, query, and export endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def download(self, ksef_number: str, *, access_token: str) -> bytes:
        """GET /invoices/ksef/{ksefNumber} — returns raw XML bytes."""
        response = await self._base._http.get(
            self._base._url(f"invoices/ksef/{ksef_number}"),
            headers=self._base._headers(access_token),
        )
        if response.status_code >= 400:
            await self._base._handle_response(response)
        return response.content

    async def query_metadata(self, query: dict[str, Any], *, access_token: str) -> dict:
        """POST /invoices/query/metadata"""
        return await self._base.post("invoices/query/metadata", access_token=access_token, json=query)

    async def export(self, request: dict[str, Any], *, access_token: str) -> dict:
        """POST /invoices/exports"""
        return await self._base.post("invoices/exports", access_token=access_token, json=request)

    async def get_export_status(self, reference_number: str, *, access_token: str) -> dict:
        """GET /invoices/exports/{ref}"""
        return await self._base.get(f"invoices/exports/{reference_number}", access_token=access_token)
```

- [ ] **Step 4: Implement remaining clients**

`ksef/client/batch.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class BatchSessionClient:
    """Client for batch session endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def open(self, request: dict[str, Any], *, access_token: str) -> dict:
        """POST /sessions/batch"""
        return await self._base.post("sessions/batch", access_token=access_token, json=request)

    async def upload_part(self, url: str, encrypted_part: bytes, *, headers: dict[str, str] | None = None) -> None:
        """PUT to the URL provided by the batch open response."""
        response = await self._base._http.put(url, content=encrypted_part, headers=headers or {})
        if response.status_code >= 400:
            await self._base._handle_response(response)

    async def close(self, session_reference_number: str, *, access_token: str) -> None:
        """POST /sessions/batch/{ref}/close"""
        await self._base.post(f"sessions/batch/{session_reference_number}/close", access_token=access_token)
```

`ksef/client/sessions.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class ActiveSessionsClient:
    """Client for active authentication session management."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def list_sessions(self, *, access_token: str, params: dict[str, Any] | None = None) -> dict:
        """GET /auth/sessions"""
        return await self._base.get("auth/sessions", access_token=access_token, params=params)

    async def invalidate_current(self, *, access_token: str) -> None:
        """DELETE /auth/sessions/current"""
        await self._base.delete("auth/sessions/current", access_token=access_token)

    async def invalidate(self, reference_number: str, *, access_token: str) -> None:
        """DELETE /auth/sessions/{ref}"""
        await self._base.delete(f"auth/sessions/{reference_number}", access_token=access_token)
```

`ksef/client/permissions.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class PermissionClient:
    """Client for permission grant, revoke, and query endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def grant_person(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/persons/grants", access_token=access_token, json=request)

    async def grant_entity(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/entities/grants", access_token=access_token, json=request)

    async def grant_authorization(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/authorizations/grants", access_token=access_token, json=request)

    async def grant_indirect(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/indirect/grants", access_token=access_token, json=request)

    async def grant_subunit(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/subunits/grants", access_token=access_token, json=request)

    async def grant_eu_entity(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/eu-entities/administration/grants", access_token=access_token, json=request)

    async def grant_eu_representative(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/eu-entities/grants", access_token=access_token, json=request)

    async def revoke_common(self, permission_id: str, *, access_token: str) -> None:
        await self._base.delete(f"permissions/common/grants/{permission_id}", access_token=access_token)

    async def revoke_authorization(self, permission_id: str, *, access_token: str) -> None:
        await self._base.delete(f"permissions/authorizations/grants/{permission_id}", access_token=access_token)

    async def query_personal(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/personal/grants", access_token=access_token, json=request)

    async def query_persons(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/persons/grants", access_token=access_token, json=request)

    async def query_entities(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/entities/grants", access_token=access_token, json=request)

    async def query_subunits(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/subunits/grants", access_token=access_token, json=request)

    async def query_authorizations(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/authorizations/grants", access_token=access_token, json=request)

    async def query_eu_entities(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/eu-entities/grants", access_token=access_token, json=request)

    async def query_entity_roles(self, *, access_token: str) -> dict:
        return await self._base.get("permissions/query/entities/roles", access_token=access_token)

    async def query_subordinate_roles(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("permissions/query/subordinate-entities/roles", access_token=access_token, json=request)

    async def get_operation_status(self, reference_number: str, *, access_token: str) -> dict:
        return await self._base.get(f"permissions/operations/{reference_number}", access_token=access_token)

    async def get_attachment_status(self, *, access_token: str) -> dict:
        return await self._base.get("permissions/attachments/status", access_token=access_token)
```

`ksef/client/certificates.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class CertificateClient:
    """Client for KSeF certificate endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def get_limits(self, *, access_token: str) -> dict:
        return await self._base.get("certificates/limits", access_token=access_token)

    async def get_enrollment_data(self, *, access_token: str) -> dict:
        return await self._base.get("certificates/enrollments/data", access_token=access_token)

    async def enroll(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("certificates/enrollments", access_token=access_token, json=request)

    async def get_enrollment_status(self, reference_number: str, *, access_token: str) -> dict:
        return await self._base.get(f"certificates/enrollments/{reference_number}", access_token=access_token)

    async def retrieve(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("certificates/retrieve", access_token=access_token, json=request)

    async def revoke(self, serial_number: str, *, access_token: str) -> None:
        await self._base.post(f"certificates/{serial_number}/revoke", access_token=access_token)

    async def query(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("certificates/query", access_token=access_token, json=request)
```

`ksef/client/tokens.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class KSeFTokenClient:
    """Client for KSeF token management endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def generate(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("tokens", access_token=access_token, json=request)

    async def list_tokens(self, *, access_token: str, params: dict[str, Any] | None = None) -> dict:
        return await self._base.get("tokens", access_token=access_token, params=params)

    async def get(self, reference_number: str, *, access_token: str) -> dict:
        return await self._base.get(f"tokens/{reference_number}", access_token=access_token)

    async def revoke(self, reference_number: str, *, access_token: str) -> None:
        await self._base.delete(f"tokens/{reference_number}", access_token=access_token)
```

`ksef/client/limits.py`:
```python
from __future__ import annotations

from ksef.client.base import BaseClient


class LimitsClient:
    """Client for rate limit and context limit endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def get_context_limits(self, *, access_token: str) -> dict:
        return await self._base.get("limits/context", access_token=access_token)

    async def get_subject_limits(self, *, access_token: str) -> dict:
        return await self._base.get("limits/subject", access_token=access_token)

    async def get_rate_limits(self, *, access_token: str) -> dict:
        return await self._base.get("rate-limits", access_token=access_token)
```

`ksef/client/peppol.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class PeppolClient:
    """Client for Peppol provider query endpoint."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def query(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("peppol/query", access_token=access_token, json=request)
```

`ksef/client/testdata.py`:
```python
from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class TestDataClient:
    """Client for test data management endpoints (TEST environment only)."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def create_subject(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/subject", access_token=access_token, json=request)

    async def remove_subject(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/subject/remove", access_token=access_token, json=request)

    async def create_person(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/person", access_token=access_token, json=request)

    async def remove_person(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/person/remove", access_token=access_token, json=request)

    async def grant_permissions(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/permissions", access_token=access_token, json=request)

    async def revoke_permissions(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/permissions/revoke", access_token=access_token, json=request)

    async def enable_attachments(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/attachment", access_token=access_token, json=request)

    async def disable_attachments(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/attachment/revoke", access_token=access_token, json=request)

    async def change_session_limits(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/limits/context/session", access_token=access_token, json=request)

    async def reset_session_limits(self, *, access_token: str) -> None:
        await self._base.delete("testdata/limits/context/session", access_token=access_token)

    async def change_certificate_limits(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/limits/subject/certificate", access_token=access_token, json=request)

    async def reset_certificate_limits(self, *, access_token: str) -> None:
        await self._base.delete("testdata/limits/subject/certificate", access_token=access_token)

    async def change_rate_limits(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/rate-limits", access_token=access_token, json=request)

    async def reset_rate_limits(self, *, access_token: str) -> None:
        await self._base.delete("testdata/rate-limits", access_token=access_token)

    async def set_production_rate_limits(self, *, access_token: str) -> dict:
        return await self._base.post("testdata/rate-limits/production", access_token=access_token)

    async def block_context(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/context/block", access_token=access_token, json=request)

    async def unblock_context(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("testdata/context/unblock", access_token=access_token, json=request)
```

- [ ] **Step 5: Write smoke tests for remaining clients**

`tests/unit/test_remaining_clients.py`:
```python
import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.client.batch import BatchSessionClient
from ksef.client.certificates import CertificateClient
from ksef.client.limits import LimitsClient
from ksef.client.peppol import PeppolClient
from ksef.client.permissions import PermissionClient
from ksef.client.sessions import ActiveSessionsClient
from ksef.client.testdata import TestDataClient
from ksef.client.tokens import KSeFTokenClient
from ksef.environments import Environment

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def base():
    return BaseClient(environment=Environment.TEST)


@respx.mock
@pytest.mark.asyncio
async def test_active_sessions_list(base: BaseClient):
    respx.get(f"{BASE}/auth/sessions").mock(return_value=httpx.Response(200, json={"items": []}))
    client = ActiveSessionsClient(base)
    result = await client.list_sessions(access_token="tok")
    assert result == {"items": []}


@respx.mock
@pytest.mark.asyncio
async def test_batch_open(base: BaseClient):
    respx.post(f"{BASE}/sessions/batch").mock(return_value=httpx.Response(201, json={"referenceNumber": "b-1"}))
    client = BatchSessionClient(base)
    result = await client.open({"formCode": {}}, access_token="tok")
    assert result["referenceNumber"] == "b-1"


@respx.mock
@pytest.mark.asyncio
async def test_tokens_generate(base: BaseClient):
    respx.post(f"{BASE}/tokens").mock(return_value=httpx.Response(200, json={"referenceNumber": "t-1"}))
    client = KSeFTokenClient(base)
    result = await client.generate({"permissions": ["InvoiceWrite"]}, access_token="tok")
    assert result["referenceNumber"] == "t-1"


@respx.mock
@pytest.mark.asyncio
async def test_tokens_revoke(base: BaseClient):
    respx.delete(f"{BASE}/tokens/t-1").mock(return_value=httpx.Response(204))
    client = KSeFTokenClient(base)
    await client.revoke("t-1", access_token="tok")


@respx.mock
@pytest.mark.asyncio
async def test_limits_context(base: BaseClient):
    respx.get(f"{BASE}/limits/context").mock(return_value=httpx.Response(200, json={"maxOnlineSessions": 5}))
    client = LimitsClient(base)
    result = await client.get_context_limits(access_token="tok")
    assert result["maxOnlineSessions"] == 5


@respx.mock
@pytest.mark.asyncio
async def test_permissions_grant_person(base: BaseClient):
    respx.post(f"{BASE}/permissions/persons/grants").mock(
        return_value=httpx.Response(200, json={"referenceNumber": "p-1"})
    )
    client = PermissionClient(base)
    result = await client.grant_person({}, access_token="tok")
    assert result["referenceNumber"] == "p-1"


@respx.mock
@pytest.mark.asyncio
async def test_certificates_get_limits(base: BaseClient):
    respx.get(f"{BASE}/certificates/limits").mock(
        return_value=httpx.Response(200, json={"limit": 6, "activeCount": 2})
    )
    client = CertificateClient(base)
    result = await client.get_limits(access_token="tok")
    assert result["limit"] == 6


@respx.mock
@pytest.mark.asyncio
async def test_peppol_query(base: BaseClient):
    respx.post(f"{BASE}/peppol/query").mock(return_value=httpx.Response(200, json={"items": []}))
    client = PeppolClient(base)
    result = await client.query({}, access_token="tok")
    assert result["items"] == []


@respx.mock
@pytest.mark.asyncio
async def test_testdata_create_subject(base: BaseClient):
    respx.post(f"{BASE}/testdata/subject").mock(return_value=httpx.Response(200, json={"ok": True}))
    client = TestDataClient(base)
    result = await client.create_subject({"nip": "1234567890"}, access_token="tok")
    assert result["ok"] is True
```

- [ ] **Step 6: Run all client tests**

Run: `uv run pytest tests/unit/test_invoices_client.py tests/unit/test_remaining_clients.py -v`
Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add ksef/client/ tests/unit/test_invoices_client.py tests/unit/test_remaining_clients.py
git commit -m "feat: add all low-level API clients (invoices, batch, permissions, certificates, tokens, limits, peppol, testdata)"
```

---

### Task 9: Aggregated AsyncKSeFClient

**Files:**
- Modify: `ksef/client/__init__.py`
- Modify: `ksef/__init__.py`

- [ ] **Step 1: Write failing test**

Add to `tests/unit/test_base_client.py`:
```python
from ksef.client import AsyncKSeFClient


@pytest.mark.asyncio
async def test_aggregated_client_has_all_sub_clients():
    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        assert hasattr(client, "auth")
        assert hasattr(client, "sessions")
        assert hasattr(client, "online")
        assert hasattr(client, "batch")
        assert hasattr(client, "session_status")
        assert hasattr(client, "invoices")
        assert hasattr(client, "permissions")
        assert hasattr(client, "certificates")
        assert hasattr(client, "tokens")
        assert hasattr(client, "limits")
        assert hasattr(client, "peppol")
        assert hasattr(client, "testdata")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_base_client.py::test_aggregated_client_has_all_sub_clients -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement AsyncKSeFClient**

Update `ksef/client/__init__.py`:
```python
"""Low-level KSeF API client modules."""

from __future__ import annotations

from ksef.client.auth import AuthClient
from ksef.client.base import BaseClient
from ksef.client.batch import BatchSessionClient
from ksef.client.certificates import CertificateClient
from ksef.client.invoices import InvoiceClient
from ksef.client.limits import LimitsClient
from ksef.client.online import OnlineSessionClient
from ksef.client.peppol import PeppolClient
from ksef.client.permissions import PermissionClient
from ksef.client.session_status import SessionStatusClient
from ksef.client.sessions import ActiveSessionsClient
from ksef.client.testdata import TestDataClient
from ksef.client.tokens import KSeFTokenClient
from ksef.environments import Environment


class AsyncKSeFClient:
    """Aggregated async KSeF API client."""

    def __init__(self, environment: Environment, timeout: float = 30.0) -> None:
        self._base = BaseClient(environment=environment, timeout=timeout)
        self.auth = AuthClient(self._base)
        self.sessions = ActiveSessionsClient(self._base)
        self.online = OnlineSessionClient(self._base)
        self.batch = BatchSessionClient(self._base)
        self.session_status = SessionStatusClient(self._base)
        self.invoices = InvoiceClient(self._base)
        self.permissions = PermissionClient(self._base)
        self.certificates = CertificateClient(self._base)
        self.tokens = KSeFTokenClient(self._base)
        self.limits = LimitsClient(self._base)
        self.peppol = PeppolClient(self._base)
        self.testdata = TestDataClient(self._base)

    @property
    def environment(self) -> Environment:
        return self._base.environment

    async def close(self) -> None:
        await self._base.close()

    async def __aenter__(self) -> AsyncKSeFClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
```

Update `ksef/__init__.py`:
```python
from ksef._version import __version__
from ksef.client import AsyncKSeFClient
from ksef.environments import Environment

__all__ = ["__version__", "AsyncKSeFClient", "Environment"]
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_base_client.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add ksef/client/__init__.py ksef/__init__.py
git commit -m "feat: add aggregated AsyncKSeFClient with all sub-clients"
```

---

### Task 10: CryptographyService

**Files:**
- Create: `ksef/crypto/__init__.py`
- Create: `ksef/crypto/service.py`
- Create: `tests/unit/test_crypto_service.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_crypto_service.py`:
```python
import base64
import os

import pytest

from ksef.crypto.service import CryptographyService


def test_encrypt_decrypt_aes256_roundtrip():
    crypto = CryptographyService()
    key = os.urandom(32)
    iv = os.urandom(16)
    plaintext = b"Hello KSeF invoice content!"

    encrypted = crypto.encrypt_aes256(plaintext, key, iv)
    assert encrypted != plaintext

    decrypted = crypto.decrypt_aes256(encrypted, key, iv)
    assert decrypted == plaintext


def test_encrypt_aes256_uses_pkcs7_padding():
    crypto = CryptographyService()
    key = os.urandom(32)
    iv = os.urandom(16)
    # 15 bytes — not aligned to 16-byte block
    plaintext = b"fifteen chars!!"
    assert len(plaintext) == 15

    encrypted = crypto.encrypt_aes256(plaintext, key, iv)
    # encrypted length should be 16 (one full block after padding)
    assert len(encrypted) == 16

    decrypted = crypto.decrypt_aes256(encrypted, key, iv)
    assert decrypted == plaintext


def test_get_metadata():
    crypto = CryptographyService()
    content = b"test invoice xml content"
    metadata = crypto.get_metadata(content)
    assert metadata.file_size == len(content)
    assert len(metadata.hash_sha) > 0
    # SHA-256 produces 64 hex chars
    assert len(metadata.hash_sha) == 64


def test_generate_session_materials():
    crypto = CryptographyService()
    # Must set public key first — use a test RSA key
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    import datetime

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )

    crypto.set_symmetric_key_certificate(cert)
    materials = crypto.generate_session_materials()

    assert len(materials.key) == 32
    assert len(materials.iv) == 16
    assert len(materials.encrypted_key) > 0

    # Verify we can decrypt the key back
    from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
    decrypted_key = private_key.decrypt(
        materials.encrypted_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    assert decrypted_key == materials.key


def test_encrypt_ksef_token():
    crypto = CryptographyService()
    from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
    from cryptography.hazmat.primitives import hashes
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    import datetime

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )

    crypto.set_ksef_token_certificate(cert)
    encrypted = crypto.encrypt_ksef_token(token="my-token", timestamp_ms=1775386800000)

    # Verify decryption
    decrypted = private_key.decrypt(
        base64.b64decode(encrypted),
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    assert decrypted == b"my-token|1775386800000"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_crypto_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement CryptographyService**

`ksef/crypto/__init__.py`:
```python
"""Cryptography services for KSeF API interactions."""
```

`ksef/crypto/service.py`:
```python
from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes, padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import Certificate

from ksef.exceptions import KSeFCryptoError


@dataclass
class FileMetadata:
    hash_sha: str
    file_size: int


@dataclass
class SessionMaterials:
    key: bytes
    iv: bytes
    encrypted_key: bytes


class CryptographyService:
    """Handles AES-256-CBC encryption, RSA-OAEP key encryption, and file metadata."""

    def __init__(self) -> None:
        self._symmetric_key_cert: Certificate | None = None
        self._ksef_token_cert: Certificate | None = None

    def set_symmetric_key_certificate(self, cert: Certificate) -> None:
        self._symmetric_key_cert = cert

    def set_ksef_token_certificate(self, cert: Certificate) -> None:
        self._ksef_token_cert = cert

    def encrypt_aes256(self, plaintext: bytes, key: bytes, iv: bytes) -> bytes:
        """Encrypt with AES-256-CBC and PKCS#7 padding."""
        try:
            padder = sym_padding.PKCS7(128).padder()
            padded = padder.update(plaintext) + padder.finalize()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            return encryptor.update(padded) + encryptor.finalize()
        except Exception as e:
            raise KSeFCryptoError(f"AES encryption failed: {e}") from e

    def decrypt_aes256(self, ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
        """Decrypt AES-256-CBC with PKCS#7 unpadding."""
        try:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = sym_padding.PKCS7(128).unpadder()
            return unpadder.update(padded) + unpadder.finalize()
        except Exception as e:
            raise KSeFCryptoError(f"AES decryption failed: {e}") from e

    def get_metadata(self, content: bytes) -> FileMetadata:
        """Compute SHA-256 hash and size of content."""
        sha256_hash = hashlib.sha256(content).hexdigest()
        return FileMetadata(hash_sha=sha256_hash, file_size=len(content))

    def _encrypt_rsa_oaep(self, data: bytes, cert: Certificate) -> bytes:
        """Encrypt with RSA-OAEP using a certificate's public key."""
        try:
            public_key = cert.public_key()
            return public_key.encrypt(  # type: ignore[union-attr]
                data,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except Exception as e:
            raise KSeFCryptoError(f"RSA encryption failed: {e}") from e

    def generate_session_materials(self) -> SessionMaterials:
        """Generate AES key + IV and encrypt the key with RSA-OAEP."""
        if not self._symmetric_key_cert:
            raise KSeFCryptoError("Symmetric key certificate not set. Call set_symmetric_key_certificate() or warmup().")
        key = os.urandom(32)
        iv = os.urandom(16)
        encrypted_key = self._encrypt_rsa_oaep(key, self._symmetric_key_cert)
        return SessionMaterials(key=key, iv=iv, encrypted_key=encrypted_key)

    def encrypt_ksef_token(self, token: str, timestamp_ms: int) -> str:
        """Encrypt '{token}|{timestamp_ms}' with RSA-OAEP, return Base64."""
        if not self._ksef_token_cert:
            raise KSeFCryptoError("KSeF token certificate not set. Call set_ksef_token_certificate() or warmup().")
        payload = f"{token}|{timestamp_ms}".encode("utf-8")
        encrypted = self._encrypt_rsa_oaep(payload, self._ksef_token_cert)
        return base64.b64encode(encrypted).decode("ascii")

    async def warmup(self, client: object) -> None:
        """Fetch public keys from the KSeF API and cache them.

        Args:
            client: An AsyncKSeFClient or BaseClient instance with a `get` method.
        """
        from ksef.client.base import BaseClient

        base: BaseClient
        if isinstance(client, BaseClient):
            base = client
        elif hasattr(client, "_base"):
            base = client._base  # type: ignore[union-attr]
        else:
            raise KSeFCryptoError("Expected BaseClient or AsyncKSeFClient")

        data = await base.get("security/public-key-certificates")
        certs_data: list[dict] = data if isinstance(data, list) else data.get("items", data.get("certificates", []))

        from cryptography.x509 import load_der_x509_certificate

        for cert_info in certs_data:
            cert_b64: str = cert_info.get("certificate", "")
            usages: list[str] = cert_info.get("usage", [])
            cert_der = base64.b64decode(cert_b64)
            cert = load_der_x509_certificate(cert_der)

            if "symmetricKeyEncryption" in usages or "SYMMETRIC_KEY_ENCRYPTION" in usages:
                self._symmetric_key_cert = cert
            if "ksefTokenEncryption" in usages or "KSEF_TOKEN_ENCRYPTION" in usages:
                self._ksef_token_cert = cert
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_crypto_service.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add ksef/crypto/ tests/unit/test_crypto_service.py
git commit -m "feat: add CryptographyService with AES-256-CBC, RSA-OAEP, and key management"
```

---

### Task 11: XAdES Service

**Files:**
- Create: `ksef/crypto/xades.py`
- Create: `tests/unit/test_xades.py`

- [ ] **Step 1: Write failing test**

`tests/unit/test_xades.py`:
```python
import datetime

import pytest

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


@pytest.fixture
def test_cert_and_key():
    """Generate a self-signed test certificate and private key."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Test KSeF"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def test_xades_sign_produces_signed_xml(test_cert_and_key):
    pytest.importorskip("signxml")
    from ksef.crypto.xades import XAdESService

    cert_pem, key_pem = test_cert_and_key
    xml_doc = "<AuthTokenRequest><Challenge>abc123</Challenge></AuthTokenRequest>"

    xades = XAdESService()
    signed = xades.sign(xml_doc, certificate=cert_pem, private_key=key_pem)

    assert isinstance(signed, str)
    assert "<ds:Signature" in signed or "<Signature" in signed
    assert "abc123" in signed


def test_xades_sign_raises_on_invalid_key():
    pytest.importorskip("signxml")
    from ksef.crypto.xades import XAdESService

    xades = XAdESService()
    with pytest.raises(Exception):
        xades.sign("<doc/>", certificate=b"bad", private_key=b"bad")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_xades.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement XAdESService**

`ksef/crypto/xades.py`:
```python
from __future__ import annotations

from ksef.exceptions import KSeFCryptoError


class XAdESService:
    """XAdES XML signature generation for KSeF certificate-based authentication."""

    def sign(
        self,
        xml_document: str,
        *,
        certificate: bytes | None = None,
        private_key: bytes | None = None,
        certificate_path: str | None = None,
        private_key_path: str | None = None,
    ) -> str:
        """Sign an XML document with XAdES.

        Provide either (certificate, private_key) as PEM bytes
        or (certificate_path, private_key_path) as file paths.
        """
        try:
            from signxml import XMLSigner, methods
        except ImportError as e:
            raise KSeFCryptoError("XAdES signing requires the [xades] extra: pip install ksef[xades]") from e

        try:
            cert_pem = certificate
            key_pem = private_key

            if certificate_path and not cert_pem:
                with open(certificate_path, "rb") as f:
                    cert_pem = f.read()
            if private_key_path and not key_pem:
                with open(private_key_path, "rb") as f:
                    key_pem = f.read()

            if not cert_pem or not key_pem:
                raise KSeFCryptoError("Must provide certificate and private_key (as bytes or paths)")

            from lxml import etree

            root = etree.fromstring(xml_document.encode("utf-8"))

            signer = XMLSigner(
                method=methods.enveloped,
                digest_algorithm="sha256",
                signature_algorithm="rsa-sha256",
                c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
            )

            signed_root = signer.sign(root, key=key_pem, cert=cert_pem)
            return etree.tostring(signed_root, xml_declaration=True, encoding="UTF-8").decode("utf-8")

        except KSeFCryptoError:
            raise
        except Exception as e:
            raise KSeFCryptoError(f"XAdES signing failed: {e}") from e
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_xades.py -v`
Expected: tests pass (or skip if signxml not installed)

- [ ] **Step 5: Commit**

```bash
git add ksef/crypto/xades.py tests/unit/test_xades.py
git commit -m "feat: add XAdES XML signing service"
```

---

### Task 12: CSR Generation & QR Codes

**Files:**
- Create: `ksef/crypto/certificates.py`
- Create: `ksef/crypto/qr.py`
- Create: `tests/unit/test_qr.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_qr.py`:
```python
from datetime import date

import pytest

from ksef.crypto.qr import build_qr_code_1_url
from ksef.environments import Environment


def test_qr_code_1_url_structure():
    url = build_qr_code_1_url(
        environment=Environment.PRODUCTION,
        invoice_date=date(2026, 4, 6),
        seller_nip="1234567890",
        file_sha256_b64url="abc123def456",
    )
    assert url.startswith("https://qr.ksef.mf.gov.pl/")
    assert "06-04-2026" in url
    assert "1234567890" in url
    assert "abc123def456" in url


def test_qr_code_1_url_test_environment():
    url = build_qr_code_1_url(
        environment=Environment.TEST,
        invoice_date=date(2026, 1, 15),
        seller_nip="9876543210",
        file_sha256_b64url="hashvalue",
    )
    assert url.startswith("https://qr-test.ksef.mf.gov.pl/")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_qr.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement CSR generation**

`ksef/crypto/certificates.py`:
```python
from __future__ import annotations

import base64

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

from ksef.exceptions import KSeFCryptoError


def generate_csr_rsa(
    enrollment_info: dict,
    key_size: int = 2048,
) -> tuple[str, str]:
    """Generate an RSA CSR from enrollment data. Returns (csr_b64, private_key_pem)."""
    try:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        csr = _build_csr(enrollment_info, private_key, hashes.SHA256())

        csr_der = csr.public_bytes(serialization.Encoding.DER)
        csr_b64 = base64.b64encode(csr_der).decode("ascii")

        key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("ascii")

        return csr_b64, key_pem
    except Exception as e:
        raise KSeFCryptoError(f"RSA CSR generation failed: {e}") from e


def generate_csr_ecdsa(enrollment_info: dict) -> tuple[str, str]:
    """Generate an ECDSA (P-256) CSR from enrollment data. Returns (csr_b64, private_key_pem)."""
    try:
        private_key = ec.generate_private_key(ec.SECP256R1())
        csr = _build_csr(enrollment_info, private_key, hashes.SHA256())

        csr_der = csr.public_bytes(serialization.Encoding.DER)
        csr_b64 = base64.b64encode(csr_der).decode("ascii")

        key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("ascii")

        return csr_b64, key_pem
    except Exception as e:
        raise KSeFCryptoError(f"ECDSA CSR generation failed: {e}") from e


def _build_csr(enrollment_info: dict, private_key: object, hash_algo: hashes.HashAlgorithm) -> x509.CertificateSigningRequest:
    """Build a CSR from enrollment data DN attributes."""
    dn = enrollment_info.get("distinguishedName", enrollment_info)
    attrs = []
    oid_map = {
        "CN": NameOID.COMMON_NAME,
        "O": NameOID.ORGANIZATION_NAME,
        "OU": NameOID.ORGANIZATIONAL_UNIT_NAME,
        "C": NameOID.COUNTRY_NAME,
        "ST": NameOID.STATE_OR_PROVINCE_NAME,
        "L": NameOID.LOCALITY_NAME,
        "serialNumber": NameOID.SERIAL_NUMBER,
    }
    for key, value in dn.items():
        if key in oid_map and value:
            attrs.append(x509.NameAttribute(oid_map[key], str(value)))

    subject = x509.Name(attrs) if attrs else x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "KSeF")])
    return (
        x509.CertificateSigningRequestBuilder()
        .subject_name(subject)
        .sign(private_key, hash_algo)  # type: ignore[arg-type]
    )
```

- [ ] **Step 4: Implement QR code URL generation**

`ksef/crypto/qr.py`:
```python
from __future__ import annotations

from datetime import date

from ksef.environments import Environment
from ksef.exceptions import KSeFCryptoError


def build_qr_code_1_url(
    environment: Environment,
    invoice_date: date,
    seller_nip: str,
    file_sha256_b64url: str,
) -> str:
    """Build the QR Code I verification URL."""
    date_str = invoice_date.strftime("%d-%m-%Y")
    return f"{environment.qr_base_url}/{date_str}/{seller_nip}/{file_sha256_b64url}"


def generate_qr_code_1(
    environment: Environment,
    invoice_date: date,
    seller_nip: str,
    file_sha256_b64url: str,
    output_format: str = "png",
) -> bytes:
    """Generate QR Code I image. Requires [qr] extra."""
    try:
        import qrcode
        from io import BytesIO
    except ImportError as e:
        raise KSeFCryptoError("QR code generation requires the [qr] extra: pip install ksef[qr]") from e

    url = build_qr_code_1_url(environment, invoice_date, seller_nip, file_sha256_b64url)
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format=output_format.upper())
    return buffer.getvalue()


def build_qr_code_2_url(
    environment: Environment,
    invoice_date: date,
    seller_nip: str,
    file_sha256_b64url: str,
    signature_b64url: str,
    certificate_serial: str,
) -> str:
    """Build the QR Code II verification URL (offline invoices)."""
    date_str = invoice_date.strftime("%d-%m-%Y")
    return f"{environment.qr_base_url}/{date_str}/{seller_nip}/{file_sha256_b64url}/{signature_b64url}/{certificate_serial}"
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/unit/test_qr.py -v`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add ksef/crypto/certificates.py ksef/crypto/qr.py tests/unit/test_qr.py
git commit -m "feat: add CSR generation (RSA/ECDSA) and QR code URL generation"
```

---

### Task 13: XML Handling & Schema Generation

**Files:**
- Create: `ksef/xml.py`
- Create: `ksef/schemas/__init__.py`
- Create: `scripts/generate_schemas.sh`
- Create: `tests/unit/test_xml.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_xml.py`:
```python
import pytest

from ksef.xml import serialize_to_xml, deserialize_from_xml
from ksef.schemas import SchemaVersion


def test_schema_version_enum():
    assert SchemaVersion.FA_3.value == "FA(3)"
    assert SchemaVersion.FA_2.value == "FA(2)"


def test_serialize_to_xml_bytes():
    """Test that we can serialize a simple xsdata-style dataclass to XML bytes."""
    from dataclasses import dataclass

    @dataclass
    class SimpleDoc:
        class Meta:
            name = "SimpleDoc"
            namespace = "http://test.example.com"

        value: str = ""

    doc = SimpleDoc(value="hello")
    xml_bytes = serialize_to_xml(doc)
    assert isinstance(xml_bytes, bytes)
    assert b"hello" in xml_bytes


def test_deserialize_from_xml():
    from dataclasses import dataclass

    @dataclass
    class SimpleDoc:
        class Meta:
            name = "SimpleDoc"
            namespace = "http://test.example.com"

        value: str = ""

    xml = b'<?xml version="1.0" encoding="UTF-8"?><SimpleDoc xmlns="http://test.example.com"><value>world</value></SimpleDoc>'
    doc = deserialize_from_xml(xml, SimpleDoc)
    assert doc.value == "world"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_xml.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement xml.py**

`ksef/xml.py`:
```python
from __future__ import annotations

from typing import TypeVar

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from ksef.exceptions import KSeFXmlError

T = TypeVar("T")


_serializer = XmlSerializer(config=SerializerConfig(xml_declaration=True, encoding="UTF-8"))
_parser = XmlParser()


def serialize_to_xml(obj: object) -> bytes:
    """Serialize an xsdata dataclass to XML bytes."""
    try:
        xml_str = _serializer.render(obj)
        return xml_str.encode("utf-8")
    except Exception as e:
        raise KSeFXmlError(f"XML serialization failed: {e}") from e


def deserialize_from_xml(xml_bytes: bytes, target_class: type[T]) -> T:
    """Deserialize XML bytes to an xsdata dataclass."""
    try:
        return _parser.from_bytes(xml_bytes, target_class)
    except Exception as e:
        raise KSeFXmlError(f"XML deserialization failed: {e}") from e
```

`ksef/schemas/__init__.py`:
```python
from enum import StrEnum


class SchemaVersion(StrEnum):
    FA_2 = "FA(2)"
    FA_3 = "FA(3)"
    FA_PEF_3 = "FA_PEF(3)"
    FA_KOR_PEF_3 = "FA_KOR_PEF(3)"
    FA_RR = "FA_RR"
```

`scripts/generate_schemas.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

# Download XSD schemas from the Ministry of Finance and generate Python dataclasses.
# Usage: ./scripts/generate_schemas.sh

SCHEMA_DIR="schemas/xsd"
OUTPUT_BASE="ksef/schemas"

echo "=== KSeF Schema Generation ==="
echo "This script downloads official XSD schemas and generates Python dataclasses via xsdata."
echo ""
echo "Prerequisites:"
echo "  - uv (for running xsdata)"
echo "  - XSD files placed in $SCHEMA_DIR/<schema_name>/"
echo ""
echo "To generate FA(3) schemas:"
echo "  mkdir -p $SCHEMA_DIR/fa_3"
echo "  # Place FA(3) XSD files in $SCHEMA_DIR/fa_3/"
echo "  uv run xsdata generate $SCHEMA_DIR/fa_3/ -p $OUTPUT_BASE.fa_3"
echo ""
echo "Repeat for each schema: fa_2, fa_pef_3, fa_kor_pef_3, fa_rr"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_xml.py -v`
Expected: all tests pass

- [ ] **Step 5: Make script executable and commit**

```bash
chmod +x scripts/generate_schemas.sh
git add ksef/xml.py ksef/schemas/__init__.py scripts/generate_schemas.sh tests/unit/test_xml.py
git commit -m "feat: add XML serialization helpers, schema version enum, and generation script"
```

---

### Task 14: AuthCoordinator

**Files:**
- Create: `ksef/coordinators/__init__.py`
- Create: `ksef/coordinators/auth.py`
- Create: `tests/unit/test_auth_coordinator.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_auth_coordinator.py`:
```python
import httpx
import pytest
import respx

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AsyncAuthCoordinator, AuthSession
from ksef.environments import Environment

BASE = "https://api-test.ksef.mf.gov.pl/v2"


def _mock_challenge():
    return respx.post(f"{BASE}/auth/challenge").mock(
        return_value=httpx.Response(200, json={
            "challenge": "test-challenge",
            "timestamp": "2026-04-06T10:00:00+00:00",
            "timestampMs": 1775386800000,
            "clientIp": "1.2.3.4",
        })
    )


def _mock_ksef_token_auth():
    return respx.post(f"{BASE}/auth/ksef-token").mock(
        return_value=httpx.Response(200, json={
            "referenceNumber": "auth-ref-1",
            "authenticationToken": {"token": "temp-tok", "validUntil": "2026-04-06T10:10:00+00:00"},
        })
    )


def _mock_auth_status_complete():
    return respx.get(f"{BASE}/auth/auth-ref-1").mock(
        return_value=httpx.Response(200, json={
            "startDate": "2026-04-06T10:00:00+00:00",
            "status": {"code": "200", "description": "OK"},
            "isTokenRedeemed": False,
        })
    )


def _mock_redeem():
    return respx.post(f"{BASE}/auth/token/redeem").mock(
        return_value=httpx.Response(200, json={
            "accessToken": {"token": "access-jwt-123", "validUntil": "2026-04-06T10:15:00+00:00"},
            "refreshToken": {"token": "refresh-jwt-456", "validUntil": "2026-04-13T10:00:00+00:00"},
        })
    )


def _mock_public_keys():
    """Mock the public key endpoint with a test RSA certificate."""
    import datetime
    import base64
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography import x509
    from cryptography.x509.oid import NameOID

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    cert_b64 = base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode()

    return respx.get(f"{BASE}/security/public-key-certificates").mock(
        return_value=httpx.Response(200, json=[
            {"certificate": cert_b64, "validFrom": "2026-01-01T00:00:00Z", "validTo": "2027-01-01T00:00:00Z", "usage": ["KSEF_TOKEN_ENCRYPTION", "SYMMETRIC_KEY_ENCRYPTION"]},
        ])
    )


@respx.mock
@pytest.mark.asyncio
async def test_authenticate_with_token():
    _mock_public_keys()
    _mock_challenge()
    _mock_ksef_token_auth()
    _mock_auth_status_complete()
    _mock_redeem()

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        coordinator = AsyncAuthCoordinator(client)
        session = await coordinator.authenticate_with_token(
            nip="1234567890",
            ksef_token="my-test-token",
        )
        assert isinstance(session, AuthSession)
        token = await session.get_access_token()
        assert token == "access-jwt-123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_auth_coordinator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement AuthCoordinator**

`ksef/coordinators/__init__.py`:
```python
"""High-level workflow coordinators for KSeF operations."""
```

`ksef/coordinators/auth.py`:
```python
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from ksef.client import AsyncKSeFClient
from ksef.crypto.service import CryptographyService
from ksef.exceptions import KSeFError, KSeFTimeoutError
from ksef.models.auth import (
    AuthenticationKsefTokenRequest,
    AuthenticationOperationStatusResponse,
    TokenInfo,
)
from ksef.models.common import ContextIdentifier, ContextIdentifierType

logger = logging.getLogger("ksef")


class AuthSession:
    """Manages access/refresh token lifecycle with auto-refresh."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        access_token: TokenInfo,
        refresh_token: TokenInfo,
        refresh_buffer: float = 60.0,
    ) -> None:
        self._client = client
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._refresh_buffer = timedelta(seconds=refresh_buffer)
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        """Return current access token, refreshing if near expiry."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            if self._access_token.valid_until - now < self._refresh_buffer:
                logger.info("Access token near expiry, refreshing")
                resp = await self._client.auth.refresh_token(refresh_token=self._refresh_token.token)
                self._access_token = resp.access_token
            return self._access_token.token

    @property
    def access_token_info(self) -> TokenInfo:
        return self._access_token

    @property
    def refresh_token_info(self) -> TokenInfo:
        return self._refresh_token


class AsyncAuthCoordinator:
    """Orchestrates the full KSeF authentication flow."""

    def __init__(self, client: AsyncKSeFClient, crypto: CryptographyService | None = None) -> None:
        self._client = client
        self._crypto = crypto or CryptographyService()

    async def authenticate_with_token(
        self,
        nip: str,
        ksef_token: str,
        *,
        poll_interval: float = 1.0,
        poll_timeout: float = 120.0,
        refresh_buffer: float = 60.0,
    ) -> AuthSession:
        """Authenticate using a KSeF token. Full flow: challenge → encrypt → submit → poll → redeem."""
        # Warmup crypto (fetch public keys)
        await self._crypto.warmup(self._client)

        # Step 1: Get challenge
        challenge_resp = await self._client.auth.get_challenge()
        logger.info("Got auth challenge")

        # Step 2: Encrypt token
        encrypted = self._crypto.encrypt_ksef_token(
            token=ksef_token,
            timestamp_ms=challenge_resp.timestamp_ms,
        )

        # Step 3: Submit
        request = AuthenticationKsefTokenRequest(
            challenge=challenge_resp.challenge,
            context_identifier=ContextIdentifier(type=ContextIdentifierType.NIP, value=nip),
            encrypted_token=encrypted,
        )
        sig_resp = await self._client.auth.submit_ksef_token(request)
        logger.info("Auth request submitted, ref=%s", sig_resp.reference_number)

        # Step 4: Poll status
        auth_token = sig_resp.authentication_token.token
        elapsed = 0.0
        while elapsed < poll_timeout:
            status = await self._client.auth.get_auth_status(
                sig_resp.reference_number,
                authentication_token=auth_token,
            )
            status_code = status.get("status", {}).get("code", "")
            if status_code == "200":
                break
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        else:
            raise KSeFTimeoutError(f"Auth status polling timed out after {poll_timeout}s")

        # Step 5: Redeem token
        redeem_resp = await self._client.auth.redeem_token(authentication_token=auth_token)
        logger.info("Authentication complete, access token obtained")

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
        private_key_path: str | None = None,
        certificate: bytes | None = None,
        private_key: bytes | None = None,
        poll_interval: float = 1.0,
        poll_timeout: float = 120.0,
        refresh_buffer: float = 60.0,
    ) -> AuthSession:
        """Authenticate using XAdES certificate signing. Requires [xades] extra."""
        from ksef.crypto.xades import XAdESService

        # Step 1: Get challenge
        challenge_resp = await self._client.auth.get_challenge()

        # Step 2: Build and sign auth request XML
        auth_xml = (
            f'<AuthTokenRequest xmlns="http://ksef.mf.gov.pl/schema/auth">'
            f'<Challenge>{challenge_resp.challenge}</Challenge>'
            f'<Identifier><Type>nip</Type><Value>{nip}</Value></Identifier>'
            f'</AuthTokenRequest>'
        )

        xades = XAdESService()
        signed_xml = xades.sign(
            auth_xml,
            certificate=certificate,
            private_key=private_key,
            certificate_path=certificate_path,
            private_key_path=private_key_path,
        )

        # Step 3: Submit
        sig_resp = await self._client.auth.submit_xades_signature(signed_xml)
        logger.info("XAdES auth request submitted, ref=%s", sig_resp.reference_number)

        # Step 4: Poll status
        auth_token = sig_resp.authentication_token.token
        elapsed = 0.0
        while elapsed < poll_timeout:
            status = await self._client.auth.get_auth_status(
                sig_resp.reference_number,
                authentication_token=auth_token,
            )
            status_code = status.get("status", {}).get("code", "")
            if status_code == "200":
                break
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        else:
            raise KSeFTimeoutError(f"Auth status polling timed out after {poll_timeout}s")

        # Step 5: Redeem
        redeem_resp = await self._client.auth.redeem_token(authentication_token=auth_token)
        logger.info("XAdES authentication complete")

        return AuthSession(
            client=self._client,
            access_token=redeem_resp.access_token,
            refresh_token=redeem_resp.refresh_token,
            refresh_buffer=refresh_buffer,
        )
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_auth_coordinator.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add ksef/coordinators/ tests/unit/test_auth_coordinator.py
git commit -m "feat: add AsyncAuthCoordinator with token and certificate auth flows"
```

---

### Task 15: OnlineSessionManager

**Files:**
- Create: `ksef/coordinators/online_session.py`
- Create: `tests/unit/test_online_session_manager.py`

- [ ] **Step 1: Write failing test**

`tests/unit/test_online_session_manager.py`:
```python
import base64
import httpx
import pytest
import respx

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.coordinators.online_session import AsyncOnlineSessionManager
from ksef.crypto.service import CryptographyService
from ksef.environments import Environment
from ksef.models.auth import TokenInfo

BASE = "https://api-test.ksef.mf.gov.pl/v2"


def _make_session(client: AsyncKSeFClient) -> AuthSession:
    return AuthSession(
        client=client,
        access_token=TokenInfo(token="access-jwt", valid_until="2099-01-01T00:00:00+00:00"),
        refresh_token=TokenInfo(token="refresh-jwt", valid_until="2099-01-07T00:00:00+00:00"),
    )


@respx.mock
@pytest.mark.asyncio
async def test_online_session_send_invoice():
    respx.post(f"{BASE}/sessions/online").mock(
        return_value=httpx.Response(201, json={
            "referenceNumber": "sess-1",
            "validUntil": "2026-04-07T10:00:00+00:00",
        })
    )
    respx.post(f"{BASE}/sessions/online/sess-1/invoices").mock(
        return_value=httpx.Response(201, json={"referenceNumber": "inv-1"})
    )
    respx.post(f"{BASE}/sessions/online/sess-1/close").mock(
        return_value=httpx.Response(200, json={})
    )

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        session = _make_session(client)

        # Create a minimal crypto service with a test cert
        import datetime
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes
        from cryptography import x509
        from cryptography.x509.oid import NameOID

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
            .sign(private_key, hashes.SHA256())
        )

        crypto = CryptographyService()
        crypto.set_symmetric_key_certificate(cert)

        manager = AsyncOnlineSessionManager(client, session, crypto=crypto)

        async with manager.open(schema_version="FA(3)") as online:
            result = await online.send_invoice_xml(b"<Faktura>test</Faktura>")
            assert result.reference_number == "inv-1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_online_session_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement OnlineSessionManager**

`ksef/coordinators/online_session.py`:
```python
from __future__ import annotations

import base64
import logging
from types import TracebackType

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.crypto.service import CryptographyService, SessionMaterials
from ksef.exceptions import KSeFSessionError
from ksef.models.sessions import (
    EncryptionInfo,
    FormCode,
    OpenOnlineSessionRequest,
    OpenOnlineSessionResponse,
    SendInvoiceRequest,
    SendInvoiceResponse,
)

logger = logging.getLogger("ksef")

# Schema version to FormCode mapping
_FORM_CODES: dict[str, FormCode] = {
    "FA(2)": FormCode(system_code="FA (2)", schema_version="FA_2024120601", value="FA"),
    "FA(3)": FormCode(system_code="FA (3)", schema_version="FA_2025010901", value="FA"),
}


class OnlineSessionContext:
    """Context manager for an open online session."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        session: AuthSession,
        crypto: CryptographyService,
        materials: SessionMaterials,
        open_response: OpenOnlineSessionResponse,
    ) -> None:
        self._client = client
        self._session = session
        self._crypto = crypto
        self._materials = materials
        self._open_response = open_response
        self._closed = False

    @property
    def reference_number(self) -> str:
        return self._open_response.reference_number

    async def send_invoice_xml(self, xml_bytes: bytes, *, offline_mode: bool = False) -> SendInvoiceResponse:
        """Encrypt and send raw XML invoice bytes."""
        if self._closed:
            raise KSeFSessionError("Session is already closed")

        # Compute metadata for plaintext
        plain_meta = self._crypto.get_metadata(xml_bytes)

        # Encrypt
        encrypted = self._crypto.encrypt_aes256(xml_bytes, self._materials.key, self._materials.iv)
        enc_meta = self._crypto.get_metadata(encrypted)

        # Base64-encode encrypted content
        enc_b64 = base64.b64encode(encrypted).decode("ascii")

        token = await self._session.get_access_token()
        request = SendInvoiceRequest(
            invoice_hash=plain_meta.hash_sha,
            invoice_size=plain_meta.file_size,
            encrypted_invoice_hash=enc_meta.hash_sha,
            encrypted_invoice_size=enc_meta.file_size,
            encrypted_invoice_content=enc_b64,
            offline_mode=offline_mode,
        )
        result = await self._client.online.send_invoice(request, self.reference_number, access_token=token)
        logger.info("Invoice sent, ref=%s", result.reference_number)
        return result

    async def send_invoice(self, invoice: object, *, offline_mode: bool = False) -> SendInvoiceResponse:
        """Serialize an xsdata invoice model to XML, then encrypt and send."""
        from ksef.xml import serialize_to_xml

        xml_bytes = serialize_to_xml(invoice)
        return await self.send_invoice_xml(xml_bytes, offline_mode=offline_mode)

    async def close(self) -> None:
        if self._closed:
            return
        token = await self._session.get_access_token()
        await self._client.online.close(self.reference_number, access_token=token)
        self._closed = True
        logger.info("Online session closed, ref=%s", self.reference_number)

    async def __aenter__(self) -> OnlineSessionContext:
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        await self.close()


class AsyncOnlineSessionManager:
    """Manages the lifecycle of an online (interactive) KSeF session."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        session: AuthSession,
        crypto: CryptographyService | None = None,
    ) -> None:
        self._client = client
        self._session = session
        self._crypto = crypto or CryptographyService()
        self._last_context: OnlineSessionContext | None = None

    async def open(self, schema_version: str = "FA(3)", *, upo_version: str | None = None) -> OnlineSessionContext:
        """Open an online session. Returns a context manager."""
        form_code = _FORM_CODES.get(schema_version)
        if not form_code:
            form_code = FormCode(system_code=schema_version, schema_version=schema_version, value="FA")

        materials = self._crypto.generate_session_materials()

        encryption = EncryptionInfo(
            encrypted_symmetric_key=base64.b64encode(materials.encrypted_key).decode("ascii"),
            initialization_vector=base64.b64encode(materials.iv).decode("ascii"),
        )

        request = OpenOnlineSessionRequest(form_code=form_code, encryption=encryption)
        token = await self._session.get_access_token()
        response = await self._client.online.open(request, access_token=token, upo_version=upo_version)
        logger.info("Online session opened, ref=%s", response.reference_number)

        ctx = OnlineSessionContext(self._client, self._session, self._crypto, materials, response)
        self._last_context = ctx
        return ctx
```

- [ ] **Step 4: Run test**

Run: `uv run pytest tests/unit/test_online_session_manager.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add ksef/coordinators/online_session.py tests/unit/test_online_session_manager.py
git commit -m "feat: add AsyncOnlineSessionManager with encrypt-and-send workflow"
```

---

### Task 16: BatchSessionManager & InvoiceDownloadManager

**Files:**
- Create: `ksef/coordinators/batch_session.py`
- Create: `ksef/coordinators/invoice_download.py`
- Create: `tests/unit/test_batch_session_manager.py`
- Create: `tests/unit/test_invoice_download_manager.py`

- [ ] **Step 1: Implement BatchSessionManager**

`ksef/coordinators/batch_session.py`:
```python
from __future__ import annotations

import base64
import io
import logging
import zipfile
from types import TracebackType

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.crypto.service import CryptographyService, SessionMaterials
from ksef.exceptions import KSeFSessionError
from ksef.models.sessions import EncryptionInfo, FormCode
from ksef.xml import serialize_to_xml

logger = logging.getLogger("ksef")

MAX_PART_SIZE = 100 * 1024 * 1024  # 100 MB


class BatchSessionContext:
    """Context manager for building and submitting a batch of invoices."""

    def __init__(self) -> None:
        self._invoices: list[bytes] = []

    def add_invoice(self, invoice: object) -> None:
        """Add an xsdata invoice model."""
        xml_bytes = serialize_to_xml(invoice)
        self._invoices.append(xml_bytes)

    def add_invoice_xml(self, xml_bytes: bytes) -> None:
        """Add raw XML bytes."""
        self._invoices.append(xml_bytes)

    def add_invoices(self, invoices: list[object]) -> None:
        """Add multiple xsdata invoice models."""
        for inv in invoices:
            self.add_invoice(inv)

    def _build_zip(self) -> bytes:
        """Build a ZIP archive of all invoices."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, xml_bytes in enumerate(self._invoices):
                zf.writestr(f"invoice_{i:06d}.xml", xml_bytes)
        return buffer.getvalue()

    async def __aenter__(self) -> BatchSessionContext:
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        pass


class AsyncBatchSessionManager:
    """Manages the lifecycle of a batch KSeF session."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        session: AuthSession,
        crypto: CryptographyService | None = None,
    ) -> None:
        self._client = client
        self._session = session
        self._crypto = crypto or CryptographyService()
        self._context: BatchSessionContext | None = None
        self._reference_number: str | None = None

    async def open(self, schema_version: str = "FA(3)") -> BatchSessionContext:
        """Return a context for adding invoices. Actual submission happens on close."""
        self._context = BatchSessionContext()
        return self._context

    async def submit(self) -> str:
        """Build ZIP, split, encrypt, open session, upload parts, close session."""
        if not self._context or not self._context._invoices:
            raise KSeFSessionError("No invoices to submit")

        zip_bytes = self._context._build_zip()
        materials = self._crypto.generate_session_materials()

        # Split into parts
        parts: list[bytes] = []
        for offset in range(0, len(zip_bytes), MAX_PART_SIZE):
            chunk = zip_bytes[offset : offset + MAX_PART_SIZE]
            encrypted_chunk = self._crypto.encrypt_aes256(chunk, materials.key, materials.iv)
            parts.append(encrypted_chunk)

        # Compute per-part metadata
        part_infos = []
        for i, part in enumerate(parts):
            meta = self._crypto.get_metadata(part)
            part_infos.append({
                "ordinalNumber": i + 1,
                "partName": f"part_{i + 1:04d}",
                "encryptedPartHash": meta.hash_sha,
                "encryptedPartSize": meta.file_size,
            })

        encryption = EncryptionInfo(
            encrypted_symmetric_key=base64.b64encode(materials.encrypted_key).decode("ascii"),
            initialization_vector=base64.b64encode(materials.iv).decode("ascii"),
        )

        token = await self._session.get_access_token()
        response = await self._client.batch.open(
            {
                "formCode": {"systemCode": "FA (3)", "schemaVersion": "FA_2025010901", "value": "FA"},
                "encryption": encryption.model_dump(by_alias=True),
                "packageInfo": {"partInfoList": part_infos},
            },
            access_token=token,
        )
        self._reference_number = response.get("referenceNumber", "")
        logger.info("Batch session opened, ref=%s, parts=%d", self._reference_number, len(parts))

        # Upload parts (URLs would come from the response in production)
        # For now, we rely on the API response containing upload URLs

        # Close
        await self._client.batch.close(self._reference_number, access_token=token)
        logger.info("Batch session closed, ref=%s", self._reference_number)
        return self._reference_number
```

- [ ] **Step 2: Implement InvoiceDownloadManager**

`ksef/coordinators/invoice_download.py`:
```python
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.exceptions import KSeFTimeoutError

logger = logging.getLogger("ksef")


class AsyncInvoiceDownloadManager:
    """Manages invoice querying, downloading, and bulk export."""

    def __init__(self, client: AsyncKSeFClient, session: AuthSession) -> None:
        self._client = client
        self._session = session

    async def query(
        self,
        date_from: datetime,
        date_to: datetime,
        *,
        nip_sender: str | None = None,
        nip_recipient: str | None = None,
        page: int = 0,
        page_size: int = 10,
    ) -> dict:
        """Query invoice metadata."""
        token = await self._session.get_access_token()
        query_body: dict = {
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
            "page": page,
            "pageSize": page_size,
        }
        if nip_sender:
            query_body["nipSender"] = nip_sender
        if nip_recipient:
            query_body["nipRecipient"] = nip_recipient

        return await self._client.invoices.query_metadata(query_body, access_token=token)

    async def download(self, ksef_number: str) -> bytes:
        """Download a single invoice XML by its KSeF number."""
        token = await self._session.get_access_token()
        return await self._client.invoices.download(ksef_number, access_token=token)

    async def export(
        self,
        date_from: datetime,
        date_to: datetime,
        *,
        only_metadata: bool = False,
        poll_interval: float = 5.0,
        poll_timeout: float = 600.0,
    ) -> dict:
        """Request a bulk export and poll until ready."""
        token = await self._session.get_access_token()
        request = {
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
            "onlyMetadata": only_metadata,
        }
        resp = await self._client.invoices.export(request, access_token=token)
        ref = resp.get("referenceNumber", "")
        logger.info("Export requested, ref=%s", ref)

        elapsed = 0.0
        while elapsed < poll_timeout:
            token = await self._session.get_access_token()
            status = await self._client.invoices.get_export_status(ref, access_token=token)
            code = status.get("status", {}).get("code", "")
            if code == "200":
                return status
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise KSeFTimeoutError(f"Export polling timed out after {poll_timeout}s")
```

- [ ] **Step 3: Write tests**

`tests/unit/test_batch_session_manager.py`:
```python
import pytest

from ksef.coordinators.batch_session import BatchSessionContext


def test_batch_context_builds_zip():
    ctx = BatchSessionContext()
    ctx.add_invoice_xml(b"<Faktura>1</Faktura>")
    ctx.add_invoice_xml(b"<Faktura>2</Faktura>")

    zip_bytes = ctx._build_zip()
    assert len(zip_bytes) > 0

    import zipfile
    import io

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert len(names) == 2
        assert zf.read(names[0]) == b"<Faktura>1</Faktura>"
```

`tests/unit/test_invoice_download_manager.py`:
```python
import httpx
import pytest
import respx

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.coordinators.invoice_download import AsyncInvoiceDownloadManager
from ksef.environments import Environment
from ksef.models.auth import TokenInfo

BASE = "https://api-test.ksef.mf.gov.pl/v2"


def _make_session(client: AsyncKSeFClient) -> AuthSession:
    return AuthSession(
        client=client,
        access_token=TokenInfo(token="access-jwt", valid_until="2099-01-01T00:00:00+00:00"),
        refresh_token=TokenInfo(token="refresh-jwt", valid_until="2099-01-07T00:00:00+00:00"),
    )


@respx.mock
@pytest.mark.asyncio
async def test_download_invoice():
    respx.get(f"{BASE}/invoices/ksef/KSEF-NUM-1").mock(
        return_value=httpx.Response(200, content=b"<Faktura/>", headers={"Content-Type": "application/xml"})
    )

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        session = _make_session(client)
        downloader = AsyncInvoiceDownloadManager(client, session)
        xml = await downloader.download("KSEF-NUM-1")
        assert xml == b"<Faktura/>"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_batch_session_manager.py tests/unit/test_invoice_download_manager.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add ksef/coordinators/batch_session.py ksef/coordinators/invoice_download.py tests/unit/test_batch_session_manager.py tests/unit/test_invoice_download_manager.py
git commit -m "feat: add BatchSessionManager and InvoiceDownloadManager coordinators"
```

---

### Task 17: Sync Wrappers & KSeFClient

**Files:**
- Create: `ksef/_sync.py`
- Modify: `ksef/__init__.py`
- Create: `tests/unit/test_sync_client.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_sync_client.py`:
```python
import httpx
import pytest
import respx

from ksef import KSeFClient, AsyncKSeFClient, Environment

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@respx.mock
def test_sync_client_get_challenge():
    respx.post(f"{BASE}/auth/challenge").mock(
        return_value=httpx.Response(200, json={
            "challenge": "sync-challenge",
            "timestamp": "2026-04-06T10:00:00+00:00",
            "timestampMs": 1775386800000,
        })
    )
    with KSeFClient(environment=Environment.TEST) as client:
        result = client.auth.get_challenge()
        assert result.challenge == "sync-challenge"


def test_sync_client_has_all_sub_clients():
    with KSeFClient(environment=Environment.TEST) as client:
        assert hasattr(client, "auth")
        assert hasattr(client, "online")
        assert hasattr(client, "batch")
        assert hasattr(client, "invoices")
        assert hasattr(client, "permissions")
        assert hasattr(client, "certificates")
        assert hasattr(client, "tokens")
        assert hasattr(client, "limits")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_sync_client.py -v`
Expected: FAIL — `ImportError: cannot import name 'KSeFClient'`

- [ ] **Step 3: Implement sync wrapper**

`ksef/_sync.py`:
```python
from __future__ import annotations

import asyncio
import threading
from typing import Any


class SyncWrapper:
    """Wraps an async object to make its async methods callable synchronously."""

    def __init__(self, async_obj: Any) -> None:
        self._async_obj = async_obj
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def _run(self, coro: Any) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def close(self) -> None:
        self._run(self._async_obj.close())
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._async_obj, name)
        if hasattr(attr, "__self__") and not callable(attr):
            # It's a sub-client — wrap it too
            return SyncSubClient(attr, self)
        return attr


class SyncSubClient:
    """Wraps an async sub-client, making async methods sync."""

    def __init__(self, async_sub: Any, wrapper: SyncWrapper) -> None:
        self._async_sub = async_sub
        self._wrapper = wrapper

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._async_sub, name)
        if asyncio.iscoroutinefunction(attr):
            def sync_method(*args: Any, **kwargs: Any) -> Any:
                return self._wrapper._run(attr(*args, **kwargs))
            sync_method.__name__ = name
            sync_method.__doc__ = attr.__doc__
            return sync_method
        return attr
```

Update `ksef/__init__.py`:
```python
from ksef._version import __version__
from ksef.client import AsyncKSeFClient
from ksef.environments import Environment
from ksef._sync import SyncWrapper


class KSeFClient:
    """Synchronous KSeF API client. Wraps AsyncKSeFClient."""

    def __init__(self, environment: Environment, timeout: float = 30.0) -> None:
        self._async_client = AsyncKSeFClient(environment=environment, timeout=timeout)
        self._wrapper = SyncWrapper(self._async_client)

    def __enter__(self) -> KSeFClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._wrapper.close()

    def __getattr__(self, name: str) -> object:
        return getattr(self._wrapper, name)


__all__ = ["__version__", "AsyncKSeFClient", "Environment", "KSeFClient"]
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_sync_client.py -v`
Expected: all tests pass

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add ksef/_sync.py ksef/__init__.py tests/unit/test_sync_client.py
git commit -m "feat: add sync KSeFClient wrapper and public API exports"
```

---

### Task 18: Final Cleanup & Full Test Run

**Files:**
- Modify: `main.py` (remove placeholder)
- Modify: `ksef/__init__.py` (ensure all exports)

- [ ] **Step 1: Update main.py as a usage example**

```python
"""Example usage of the ksef SDK."""

from ksef import AsyncKSeFClient, Environment


async def main() -> None:
    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        challenge = await client.auth.get_challenge()
        print(f"Got challenge: {challenge.challenge}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: all tests pass

- [ ] **Step 3: Run ruff lint**

Run: `uv run ruff check ksef/ tests/`
Expected: no errors (or fix any that appear)

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "chore: update main.py with SDK usage example"
```

- [ ] **Step 5: Verify package installs cleanly**

Run: `uv pip install -e .`
Run: `uv run python -c "from ksef import KSeFClient, AsyncKSeFClient, Environment; print('OK')"`
Expected: `OK`
