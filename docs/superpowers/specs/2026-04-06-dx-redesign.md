# KSeF SDK DX Redesign — Design Specification

**Date**: 2026-04-06
**Status**: Approved

## Overview

Replace the multi-layer public API (AsyncKSeFClient, coordinators, CryptographyService) with a single `KSeF` / `AsyncKSeF` class that handles auth, crypto, sessions, and all operations internally. The goal: sending an invoice is 3 lines, not 15.

## Before / After

**Before (current):**
```python
from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.coordinators.online_session import AsyncOnlineSessionManager

async with AsyncKSeFClient(environment=Environment.TEST) as client:
    auth = AsyncAuthCoordinator(client)
    session = await auth.authenticate_with_certificate(nip=nip, certificate=cert, private_key=key)
    crypto = await auth._get_or_create_crypto()
    manager = AsyncOnlineSessionManager(client, session, crypto=crypto)
    async with manager.open(schema_version="FA(3)") as online:
        result = await online.send_invoice_xml(xml_bytes)
```

**After (new):**
```python
from ksef import KSeF

with KSeF(nip="1234567890", token="your-token", env="test") as client:
    result = client.send_invoice(xml_bytes)
```

## Public API Surface

### Exports

```python
# ksef/__init__.py exports ONLY:
from ksef import KSeF, AsyncKSeF, Environment
from ksef.exceptions import *
from ksef.testing import *
```

Everything else is internal implementation.

### Constructor

```python
KSeF(
    nip: str,                              # required
    *,
    token: str | None = None,              # KSeF token auth
    cert: str | bytes | None = None,       # certificate path or PEM bytes
    key: str | bytes | None = None,        # private key path or PEM bytes
    env: str | Environment = "production", # "test", "demo", "production", or Environment
    timeout: float = 30.0,
)
```

- Must provide `nip`
- Must provide `token` OR (`cert` + `key`), not both, not neither
- `env` accepts string shorthand or `Environment` object
- Raises `ValueError` on invalid args (no network call)
- Auth is lazy — first API call triggers authentication
- Crypto warmup cached for client lifetime

### Methods

```python
class AsyncKSeF:
    # Invoice operations
    async def send_invoice(xml: bytes, *, offline: bool = False) -> InvoiceResult
    async def send_invoices(xmls: list[bytes]) -> list[InvoiceResult]
    async def download_invoice(ksef_number: str) -> bytes
    async def query_invoices(**filters) -> list[InvoiceMetadata]
    async def export_invoices(**filters) -> ExportResult

    # Session context for efficient multi-send
    def session(schema: str = "FA(3)") -> AsyncSessionContext

    # Token management
    async def create_token(permissions: list[str], description: str) -> TokenResult
    async def list_tokens() -> list[TokenInfo]
    async def revoke_token(reference: str) -> None

    # Permissions
    async def query_permissions() -> list
    async def get_attachment_status() -> dict

    # Certificates
    async def get_certificate_limits() -> dict
    async def get_enrollment_data() -> dict

    # Limits (combines context + subject + rate in one call)
    async def get_limits() -> LimitsInfo

    # Session status
    async def get_session_status(reference: str) -> SessionStatus

    # QR code
    def qr_url(invoice_date, seller_nip, file_hash) -> str

    # Lifecycle
    async def close() -> None
    async def __aenter__() -> AsyncKSeF
    async def __aexit__() -> None
```

`KSeF` (sync) has identical methods without `async`/`await`.

### Session Context

```python
# Standalone send — opens session, sends, closes automatically
result = client.send_invoice(xml_bytes)

# Multi-send — one session, multiple invoices
with client.session() as s:
    r1 = s.send(xml1)
    r2 = s.send(xml2)
    s.results       # [r1, r2]
    s.reference_number  # session ref
# session auto-closes
```

### Return Types

All new dataclasses — no raw dicts in public API.

```python
@dataclass
class InvoiceResult:
    reference_number: str
    ksef_number: str | None  # None if not yet assigned
    status: str              # "sent", "accepted", "rejected"

@dataclass
class TokenResult:
    reference_number: str
    token: str

@dataclass
class LimitsInfo:
    context: dict
    subject: dict
    rate: dict

@dataclass
class SessionStatus:
    code: int
    description: str
    invoice_count: int | None
    successful_count: int | None
    failed_count: int | None
```

### Exceptions

```python
KSeFError                    # base
├── KSeFAuthError            # 401, challenge expired, token invalid
├── KSeFInvoiceError         # 400/450 on invoice send with validation details
├── KSeFPermissionError      # 403
├── KSeFRateLimitError       # 429 with retry_after
├── KSeFSessionError         # session lifecycle errors
├── KSeFServerError          # 5xx
└── KSeFTimeoutError         # polling timeouts
```

Every exception has:
- Human-readable `str()` with what went wrong + what to do
- `exc.raw_response` for debugging

### Authentication Flow (internal)

Lazy — triggered on first API call:

1. Check if authenticated (has valid access token)
2. If not: warmup crypto → get challenge → encrypt token / sign XAdES → submit → poll → redeem
3. Cache access token, auto-refresh before expiry
4. All subsequent calls use cached token

## File Changes

### New files
- `ksef/easy.py` — `AsyncKSeF` implementation (the core)
- `ksef/result.py` — `InvoiceResult`, `TokenResult`, `LimitsInfo`, `SessionStatus` dataclasses

### Rewritten files
- `ksef/__init__.py` — exports only `KSeF`, `AsyncKSeF`, `Environment`
- `ksef/exceptions.py` — simplified hierarchy with better messages
- `README.md` — complete rewrite
- All `examples/*.py` — use new API
- All `tests/unit/*.py` — use new API
- All `tests/integration/*.py` — use new API

### Internal (unchanged, just no longer public)
- `ksef/client/` — all sub-clients
- `ksef/coordinators/` — all coordinators
- `ksef/crypto/` — crypto service, xades, qr, certificates
- `ksef/models/` — Pydantic models
- `ksef/_sync.py` — sync wrapper machinery
- `ksef/xml.py` — XML helpers
- `ksef/schemas/` — schema version enum

## Testing

```bash
uv run pytest tests/unit/ -v      # unit tests with new API
uv run pytest tests/integration/ -m integration -v  # integration tests
uv run python examples/02_authenticate_certificate.py  # smoke test
```
