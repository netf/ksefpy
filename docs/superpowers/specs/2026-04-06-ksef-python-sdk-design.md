# KSeF Python SDK — Design Specification

**Date**: 2026-04-06
**Status**: Approved
**Package name**: `ksef`
**Repository**: ksefpy

## Overview

A modern Python SDK for the Polish National e-Invoice System (KSeF) API 2.0. Provides full API coverage with both low-level endpoint access and high-level workflow coordinators. Async-first with sync convenience wrappers.

**Reference implementations:**
- [ksef-docs](https://github.com/CIRFMF/ksef-docs) — official KSeF 2.0 integration guide
- [ksef-client-csharp](https://github.com/CIRFMF/ksef-client-csharp) — official C# client (architectural reference)

## Constraints

- Python >=3.12
- Async-first, sync wrappers without code duplication
- Invoice XML models generated from official XSD schemas via xsdata
- API request/response models hand-written as Pydantic v2 models
- HTTP client hand-written on httpx
- Heavy dependencies (crypto, QR) gated behind extras

## Package Structure

```
ksef/
├── __init__.py              # Public API: KSeFClient, AsyncKSeFClient, Environment
├── py.typed                 # PEP 561 marker
├── _version.py              # Version string
│
├── client/                  # Low-level API client
│   ├── __init__.py
│   ├── base.py              # BaseClient (httpx wrapper, auth headers, retries, error handling)
│   ├── auth.py              # AuthClient (challenge, xades, ksef-token, status, redeem, refresh)
│   ├── sessions.py          # ActiveSessionsClient (list, invalidate)
│   ├── online.py            # OnlineSessionClient (open, send invoice, close)
│   ├── batch.py             # BatchSessionClient (open, upload part, close)
│   ├── invoices.py          # InvoiceClient (download by KSeF number, query metadata, exports)
│   ├── session_status.py    # SessionStatusClient (session status, invoice status, UPO)
│   ├── permissions.py       # PermissionClient (grant, revoke, search, operations)
│   ├── certificates.py      # CertificateClient (limits, enroll, retrieve, revoke, query)
│   ├── tokens.py            # KSeFTokenClient (generate, list, get, revoke)
│   ├── limits.py            # LimitsClient (context, subject, rate limits)
│   ├── peppol.py            # PeppolClient (query providers)
│   └── testdata.py          # TestDataClient (subjects, persons, permissions, limits)
│
├── coordinators/            # High-level workflow orchestrators
│   ├── __init__.py
│   ├── auth.py              # AuthCoordinator / AsyncAuthCoordinator
│   ├── online_session.py    # OnlineSessionManager / AsyncOnlineSessionManager
│   ├── batch_session.py     # BatchSessionManager / AsyncBatchSessionManager
│   └── invoice_download.py  # InvoiceDownloadManager / AsyncInvoiceDownloadManager
│
├── crypto/                  # Cryptography services (base; XAdES requires [xades] extra)
│   ├── __init__.py
│   ├── service.py           # CryptographyService (AES-256-CBC, RSA-OAEP, key management)
│   ├── xades.py             # XAdES signature generation
│   ├── certificates.py      # CSR generation (RSA & ECDSA), certificate fetching
│   └── qr.py                # QR Code I & II generation (requires [qr] extra)
│
├── models/                  # Pydantic v2 models for API requests/responses
│   ├── __init__.py
│   ├── auth.py              # Challenge, TokenRequest/Response, SignatureResponse
│   ├── sessions.py          # OpenSession, SendInvoice, SessionStatus
│   ├── invoices.py          # InvoiceMetadata, ExportRequest/Response
│   ├── permissions.py       # Grant/Revoke/Query requests and responses
│   ├── certificates.py      # Enrollment, Limits, Query models
│   ├── tokens.py            # KSeFToken, TokenInfo, permissions
│   ├── limits.py            # ContextLimits, SubjectLimits, RateLimits
│   ├── common.py            # ContextIdentifier, SubjectIdentifier, pagination
│   └── errors.py            # ApiError, ProblemDetails (RFC 7807)
│
├── schemas/                 # XSD-generated invoice dataclasses (via xsdata)
│   ├── __init__.py
│   ├── fa_2/                # FA(2) schema — TEST only
│   ├── fa_3/                # FA(3) schema — all environments
│   ├── fa_pef_3/            # FA_PEF(3) schema
│   ├── fa_kor_pef_3/        # FA_KOR_PEF(3) schema
│   └── fa_rr/               # FA_RR schema
│
├── environments.py          # TEST, DEMO, PRODUCTION presets
├── exceptions.py            # Typed exception hierarchy
└── xml.py                   # XML serialization/deserialization helpers
```

## Dependencies

| Dependency | Extra | Purpose |
|---|---|---|
| `httpx` | base | HTTP client (sync + async) |
| `pydantic>=2` | base | API request/response validation |
| `xsdata` | base | XML <-> dataclass serialization for invoice schemas |
| `cryptography` | base | AES-256-CBC, RSA-OAEP (required for all auth methods and invoice encryption) |
| `signxml` | `[xades]` | XAdES signature generation for certificate-based auth |
| `qrcode` | `[qr]` | QR Code I & II generation |
| `Pillow` | `[qr]` | QR image rendering |

Note: `cryptography` is a base dependency because even KSeF token auth requires
RSA-OAEP encryption, and invoice submission requires AES-256-CBC encryption.
XAdES signing is the only auth method that needs an additional dependency (`signxml`).

Install variants:
- `pip install ksef` — full functionality (all auth methods except XAdES, all sessions, invoices, crypto)
- `pip install ksef[xades]` — adds XAdES certificate-based auth via signxml
- `pip install ksef[qr]` — adds QR code generation
- `pip install ksef[all]` — everything

## Environments

Three presets matching official KSeF infrastructure:

```python
@dataclass(frozen=True)
class Environment:
    name: str
    api_base_url: str          # e.g. "https://api-test.ksef.mf.gov.pl/v2"
    qr_base_url: str           # e.g. "https://qr-test.ksef.mf.gov.pl"
    # Public keys fetched via GET {api_base_url}/security/public-key-certificates

    TEST = ...       # https://api-test.ksef.mf.gov.pl/v2
    DEMO = ...       # https://api-demo.ksef.mf.gov.pl/v2
    PRODUCTION = ... # https://api.ksef.mf.gov.pl/v2
```

## Client Initialization

```python
client = KSeFClient(
    environment=Environment.TEST,
    timeout=30.0,
    max_retries=3,
    nip="1234567890",  # optional default NIP context
)
```

The client holds no auth state — tokens are passed explicitly to methods or managed by coordinators. This keeps the client stateless and thread-safe.

Public key fetching happens lazily via `CryptographyService` on first use, cached with TTL.

## Low-Level Client API

Each sub-client maps 1:1 to KSeF API endpoints. All methods accept and return Pydantic models. Access tokens are passed as keyword arguments.

```python
class AsyncKSeFClient:
    auth: AuthClient
    sessions: ActiveSessionsClient
    online: OnlineSessionClient
    batch: BatchSessionClient
    invoices: InvoiceClient
    session_status: SessionStatusClient
    permissions: PermissionClient
    certificates: CertificateClient
    tokens: KSeFTokenClient
    limits: LimitsClient
    peppol: PeppolClient
    testdata: TestDataClient
```

Usage:
```python
async with AsyncKSeFClient(environment=Environment.TEST) as client:
    challenge = await client.auth.get_challenge()
```

### API Endpoint Coverage

**Auth** (`client.auth`):
- `get_challenge()` — POST /auth/challenge
- `submit_xades_signature(signed_xml, *, access_token)` — POST /auth/xades-signature
- `submit_ksef_token(request)` — POST /auth/ksef-token
- `get_auth_status(reference_number, *, authentication_token)` — GET /auth/{ref}
- `redeem_token(*, authentication_token)` — POST /auth/token/redeem
- `refresh_token(*, refresh_token)` — POST /auth/token/refresh

**Active Sessions** (`client.sessions`):
- `list_sessions(*, access_token, page, page_size)` — GET /auth/sessions
- `invalidate_current(*, access_token)` — DELETE /auth/sessions/current
- `invalidate(reference_number, *, access_token)` — DELETE /auth/sessions/{ref}

**Online Sessions** (`client.online`):
- `open(request, *, access_token, upo_version)` — POST /sessions/online
- `send_invoice(request, session_ref, *, access_token)` — POST /sessions/online/{ref}/invoices
- `close(session_ref, *, access_token)` — POST /sessions/online/{ref}/close

**Batch Sessions** (`client.batch`):
- `open(request, *, access_token)` — POST /sessions/batch
- `upload_part(url, encrypted_part, *, headers)` — PUT (URL from open response)
- `close(session_ref, *, access_token)` — POST /sessions/batch/{ref}/close

**Invoices** (`client.invoices`):
- `download(ksef_number, *, access_token)` — GET /invoices/ksef/{ksefNumber}
- `query_metadata(request, *, access_token)` — POST /invoices/query/metadata
- `export(request, *, access_token)` — POST /invoices/exports
- `get_export_status(reference_number, *, access_token)` — GET /invoices/exports/{ref}

**Session Status** (`client.session_status`):
- `get_session_status(reference_number, *, access_token)` — GET /sessions/{ref}
- `get_session_invoices(reference_number, *, access_token)` — GET /sessions/{ref}/invoices
- `get_failed_invoices(reference_number, *, access_token)` — GET /sessions/{ref}/invoices/failed
- `get_invoice_status(session_ref, invoice_ref, *, access_token)` — GET /sessions/{ref}/invoices/{invoiceRef}
- `get_upo(session_ref, upo_ref, *, access_token)` — GET /sessions/{ref}/upo/{upoRef}

**Permissions** (`client.permissions`):
- `grant_person(request, *, access_token)` — POST /permissions/persons/grants
- `grant_entity(request, *, access_token)` — POST /permissions/entities/grants
- `grant_authorization(request, *, access_token)` — POST /permissions/authorizations/grants
- `grant_indirect(request, *, access_token)` — POST /permissions/indirect/grants
- `grant_subunit(request, *, access_token)` — POST /permissions/subunits/grants
- `grant_eu_entity(request, *, access_token)` — POST /permissions/eu-entities/administration/grants
- `grant_eu_representative(request, *, access_token)` — POST /permissions/eu-entities/grants
- `revoke_common(permission_id, *, access_token)` — DELETE /permissions/common/grants/{id}
- `revoke_authorization(permission_id, *, access_token)` — DELETE /permissions/authorizations/grants/{id}
- `query_personal(request, *, access_token)` — POST /permissions/query/personal/grants
- `query_persons(request, *, access_token)` — POST /permissions/query/persons/grants
- `query_entities(request, *, access_token)` — POST /permissions/query/entities/grants
- `query_subunits(request, *, access_token)` — POST /permissions/query/subunits/grants
- `query_authorizations(request, *, access_token)` — POST /permissions/query/authorizations/grants
- `query_eu_entities(request, *, access_token)` — POST /permissions/query/eu-entities/grants
- `query_entity_roles(*, access_token)` — GET /permissions/query/entities/roles
- `query_subordinate_roles(request, *, access_token)` — POST /permissions/query/subordinate-entities/roles
- `get_operation_status(reference_number, *, access_token)` — GET /permissions/operations/{ref}
- `get_attachment_status(*, access_token)` — GET /permissions/attachments/status

**Certificates** (`client.certificates`):
- `get_limits(*, access_token)` — GET /certificates/limits
- `get_enrollment_data(*, access_token)` — GET /certificates/enrollments/data
- `enroll(request, *, access_token)` — POST /certificates/enrollments
- `get_enrollment_status(reference_number, *, access_token)` — GET /certificates/enrollments/{ref}
- `retrieve(request, *, access_token)` — POST /certificates/retrieve
- `revoke(serial_number, *, access_token)` — POST /certificates/{serial}/revoke
- `query(request, *, access_token)` — POST /certificates/query

**KSeF Tokens** (`client.tokens`):
- `generate(request, *, access_token)` — POST /tokens
- `list_tokens(*, access_token, params)` — GET /tokens
- `get(reference_number, *, access_token)` — GET /tokens/{ref}
- `revoke(reference_number, *, access_token)` — DELETE /tokens/{ref}

**Limits** (`client.limits`):
- `get_context_limits(*, access_token)` — GET /limits/context
- `get_subject_limits(*, access_token)` — GET /limits/subject
- `get_rate_limits(*, access_token)` — GET /rate-limits

**Peppol** (`client.peppol`):
- `query(request, *, access_token)` — POST /peppol/query

**Test Data** (`client.testdata`):
- `create_subject(request, *, access_token)` — POST /testdata/subject
- `remove_subject(request, *, access_token)` — POST /testdata/subject/remove
- `create_person(request, *, access_token)` — POST /testdata/person
- `remove_person(request, *, access_token)` — POST /testdata/person/remove
- `grant_permissions(request, *, access_token)` — POST /testdata/permissions
- `revoke_permissions(request, *, access_token)` — POST /testdata/permissions/revoke
- `enable_attachments(request, *, access_token)` — POST /testdata/attachment
- `disable_attachments(request, *, access_token)` — POST /testdata/attachment/revoke
- `change_session_limits(request, *, access_token)` — POST /testdata/limits/context/session
- `reset_session_limits(*, access_token)` — DELETE /testdata/limits/context/session
- `change_certificate_limits(request, *, access_token)` — POST /testdata/limits/subject/certificate
- `reset_certificate_limits(*, access_token)` — DELETE /testdata/limits/subject/certificate
- `change_rate_limits(request, *, access_token)` — POST /testdata/rate-limits
- `reset_rate_limits(*, access_token)` — DELETE /testdata/rate-limits
- `set_production_rate_limits(*, access_token)` — POST /testdata/rate-limits/production
- `block_context(request, *, access_token)` — POST /testdata/context/block
- `unblock_context(request, *, access_token)` — POST /testdata/context/unblock

## High-Level Coordinators

### AuthCoordinator

Full authentication lifecycle with auto token refresh.

```python
auth = AsyncAuthCoordinator(client)

# KSeF token auth
session = await auth.authenticate_with_token(nip="1234567890", ksef_token="...")

# XAdES certificate auth (requires [xades])
session = await auth.authenticate_with_certificate(
    nip="1234567890",
    certificate_path="/path/to/cert.pem",
    private_key_path="/path/to/key.pem",
)

# AuthSession manages token lifecycle
access_token = await session.get_access_token()  # auto-refreshes before expiry
```

Internal flow:
1. `get_challenge()` — obtain challenge (10 min validity)
2. Encrypt token or sign XML with XAdES
3. `submit_ksef_token()` or `submit_xades_signature()`
4. Poll `get_auth_status()` until complete
5. `redeem_token()` — obtain access_token + refresh_token
6. Background refresh before JWT expiry (configurable buffer, default 60s)

### OnlineSessionManager

Send individual invoices in an interactive session.

```python
manager = AsyncOnlineSessionManager(client, session)

async with manager.open(schema_version="FA(3)") as online:
    result = await online.send_invoice(invoice)       # xsdata model
    result = await online.send_invoice_xml(xml_bytes)  # raw XML
# auto-closes on exit

upo = await manager.get_upo(poll_interval=2.0, timeout=60.0)
```

Internal flow per invoice:
1. Generate AES-256 key + IV
2. Encrypt symmetric key with RSA-OAEP (Ministry public key)
3. Serialize invoice to XML (xsdata)
4. Encrypt invoice with AES-256-CBC
5. Compute SHA-256 hashes and file sizes (plaintext + encrypted)
6. POST to sessions/online/{ref}/invoices
7. On close: poll for UPO

### BatchSessionManager

Bulk invoice submission via ZIP.

```python
manager = AsyncBatchSessionManager(client, session)

async with manager.open(schema_version="FA(3)") as batch:
    batch.add_invoice(invoice1)
    batch.add_invoices([invoice2, invoice3])
# auto: builds ZIP, splits <=100MB parts, encrypts, uploads, closes

upo = await manager.get_upo(poll_interval=5.0, timeout=300.0)
```

### InvoiceDownloadManager

Query and retrieve invoices.

```python
downloader = AsyncInvoiceDownloadManager(client, session)

invoices = await downloader.query(
    date_from=datetime(2026, 1, 1),
    date_to=datetime(2026, 3, 31),
    nip_sender="9876543210",
)

xml_bytes = await downloader.download("1234567890-20260101-ABC123-DE")

export = await downloader.export(
    date_from=datetime(2026, 1, 1),
    date_to=datetime(2026, 3, 31),
    only_metadata=False,
    poll_interval=5.0,
)
```

## Cryptography Service

Base dependency. Used internally by coordinators, also exposed for advanced users. XAdES signing requires the `[xades]` extra.

```python
crypto = CryptographyService(client)
await crypto.warmup()  # fetches Ministry public keys, caches with TTL

# Session materials
materials = crypto.generate_session_materials()
# -> .key (32 bytes), .iv (16 bytes), .encrypted_key (RSA-OAEP encrypted)

# AES-256-CBC
encrypted = crypto.encrypt_aes256(plaintext, key, iv)
decrypted = crypto.decrypt_aes256(ciphertext, key, iv)
await crypto.encrypt_aes256_stream(input, output, key, iv)
await crypto.decrypt_aes256_stream(input, output, key, iv)

# RSA-OAEP
encrypted_key = crypto.encrypt_symmetric_key(key_bytes)
encrypted_token = crypto.encrypt_ksef_token(token="...", timestamp_ms=...)

# File metadata
metadata = crypto.get_metadata(file_bytes)  # -> FileMetadata(sha256, size)
```

### XAdES Signing

```python
xades = XAdESService()
signed_xml = xades.sign(xml_document, certificate_path="...", private_key_path="...")
signed_xml = xades.sign(xml_document, certificate=cert_bytes, private_key=key_bytes)
```

### CSR Generation

```python
from ksef.crypto.certificates import generate_csr_rsa, generate_csr_ecdsa
csr_pem, private_key_pem = generate_csr_rsa(enrollment_info)
csr_pem, private_key_pem = generate_csr_ecdsa(enrollment_info)
```

### QR Code Generation

Requires `[qr]` extra.

```python
from ksef.crypto.qr import generate_qr_code_1, generate_qr_code_2

# Code I — invoice verification (all invoices)
qr = generate_qr_code_1(
    environment=Environment.PRODUCTION,
    invoice_date=date(2026, 4, 6),
    seller_nip="1234567890",
    file_sha256=b"...",
    output_format="png",
)

# Code II — offline invoice certificate verification
qr = generate_qr_code_2(
    environment=Environment.PRODUCTION,
    invoice_date=date(2026, 4, 6),
    seller_nip="1234567890",
    file_sha256=b"...",
    certificate_path="/path/to/offline-cert.pem",
    private_key_path="/path/to/offline-key.pem",
    algorithm="rsa",  # or "ecdsa"
    output_format="png",
)
```

## XML Handling

### Invoice Schemas (xsdata-generated)

```python
from ksef.schemas.fa_3 import Faktura, FakturaWiersz, Podmiot1

invoice = Faktura(
    naglowek=Naglowek(...),
    podmiot1=Podmiot1(...),
    fa=FA(
        rodzaj_faktury="VAT",
        p_1=date(2026, 4, 6),
        fa_wiersz=[FakturaWiersz(...)],
    ),
)
```

### Serialization Helpers

```python
from ksef.xml import serialize_invoice, deserialize_invoice, validate_invoice

xml_bytes = serialize_invoice(invoice)
invoice = deserialize_invoice(xml_bytes, schema="FA(3)")
errors = validate_invoice(xml_bytes, schema="FA(3)")
```

### Schema Regeneration

Maintainer task when Ministry publishes XSD updates:

```bash
scripts/generate_schemas.sh
# Downloads XSD files, runs: uv run xsdata generate schemas/xsd/fa_3/ -p ksef.schemas.fa_3
```

Supported schemas: FA(2), FA(3), FA_PEF(3), FA_KOR_PEF(3), FA_RR.

## Sync/Async Strategy

Async-first internally. Two client classes:

```python
from ksef import AsyncKSeFClient   # async (primary)
from ksef import KSeFClient         # sync (convenience)

# Async
async with AsyncKSeFClient(environment=Environment.TEST) as client:
    challenge = await client.auth.get_challenge()

# Sync
with KSeFClient(environment=Environment.TEST) as client:
    challenge = client.auth.get_challenge()
```

`KSeFClient` wraps `AsyncKSeFClient` via `asyncio.run()` on a private event loop. Same pattern as httpx.Client vs httpx.AsyncClient.

Coordinators follow the same convention:
- `AsyncAuthCoordinator` / `AuthCoordinator`
- `AsyncOnlineSessionManager` / `OnlineSessionManager`
- `AsyncBatchSessionManager` / `BatchSessionManager`
- `AsyncInvoiceDownloadManager` / `InvoiceDownloadManager`

## Error Handling

```python
class KSeFError(Exception): ...
class KSeFApiError(KSeFError):         # HTTP 400
    status_code: int
    error_code: str | None
    details: list[ApiErrorDetail]
class KSeFUnauthorizedError(KSeFApiError): ...  # HTTP 401, RFC 7807
class KSeFForbiddenError(KSeFApiError): ...     # HTTP 403, RFC 7807
class KSeFRateLimitError(KSeFApiError):         # HTTP 429
    retry_after: float | None
    limit: int | None
    remaining: int | None
class KSeFServerError(KSeFApiError): ...        # HTTP 5xx
class KSeFCryptoError(KSeFError): ...           # encryption/signing failures
class KSeFXmlError(KSeFError):                  # XML serialization/validation
    validation_errors: list[str]
class KSeFSessionError(KSeFError): ...          # session lifecycle errors
class KSeFTimeoutError(KSeFError): ...          # polling timeouts
```

## Logging

Logger: `ksef` (standard `logging` module).

- DEBUG: HTTP request/response (URL, status, headers — no tokens or invoice content)
- INFO: Workflow milestones (session opened, invoice sent, UPO retrieved)
- WARNING: Token refresh, rate limit retry
- ERROR: API errors, crypto failures

Sensitive data (access tokens, invoice XML, encryption keys) is never logged.

## Testing

```
tests/
├── unit/                    # Fast, no network (respx mocks)
│   ├── test_models.py       # Pydantic serialization/validation
│   ├── test_crypto.py       # AES/RSA with known test vectors
│   ├── test_xml.py          # Invoice serialize/deserialize roundtrip
│   ├── test_qr.py           # QR code URL generation
│   └── test_exceptions.py   # Error parsing
│
├── integration/             # Against KSeF TEST environment
│   ├── conftest.py          # Test NIP, token, environment fixtures
│   ├── test_auth_flow.py
│   ├── test_online_session.py
│   ├── test_batch_session.py
│   ├── test_permissions.py
│   └── test_certificates.py
│
└── conftest.py              # Shared fixtures, respx setup
```

- Unit: `pytest` + `respx` + `pytest-asyncio`
- Integration: KSeF TEST environment, gated behind `--run-integration`
- CI: Unit on every push, integration on schedule

## KSeF API Reference

### Environments

| Name | API Base | QR Base |
|------|----------|---------|
| TEST | https://api-test.ksef.mf.gov.pl/v2 | https://qr-test.ksef.mf.gov.pl |
| DEMO | https://api-demo.ksef.mf.gov.pl/v2 | https://qr-demo.ksef.mf.gov.pl |
| PRODUCTION | https://api.ksef.mf.gov.pl/v2 | https://qr.ksef.mf.gov.pl |

### Rate Limits

- Standard: 100 req/s, 300 req/min, 1200 req/h
- Public key endpoints: 60 req/s
- Test data endpoints: 60 req/s

### Authentication Flow

1. POST /auth/challenge → challenge (10 min validity)
2. Encrypt token or sign XML with XAdES
3. POST /auth/ksef-token or /auth/xades-signature → authenticationToken + referenceNumber
4. Poll GET /auth/{ref} with authenticationToken until complete
5. POST /auth/token/redeem → accessToken (JWT, ~15 min) + refreshToken (up to 7 days)
6. POST /auth/token/refresh → new accessToken

### Cryptographic Requirements

- **Invoice encryption**: AES-256-CBC with PKCS#7 padding
- **Symmetric key encryption**: RSAES-OAEP (MGF1 SHA-256, SHA-256 digest)
- **Token encryption**: RSA-OAEP with SHA-256
- **XAdES**: Qualified certificate signing of XML auth request
- **QR Code II signing**: RSASSA-PSS (SHA-256, 32-byte salt) or ECDSA P-256/SHA-256
- **CSR**: PKCS#10 DER format, RSA 2048+ or EC P-256

### Session Constraints

- Interactive session validity: 12 hours
- Batch part size: ≤100 MB (before encryption)
- Batch upload timeout: 20 min per part × total parts
