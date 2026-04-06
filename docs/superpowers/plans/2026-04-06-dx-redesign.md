# DX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the multi-layer public API with a single `KSeF`/`AsyncKSeF` class that reduces invoice sending from 15 lines to 3.

**Architecture:** New `ksef/easy.py` contains `AsyncKSeF` — wraps the existing client/coordinator/crypto stack internally. `KSeF` (sync) wraps `AsyncKSeF` via `SyncWrapper`. New `ksef/result.py` contains clean return dataclasses. `ksef/__init__.py` exports only the new API. Existing internals stay untouched but become private.

**Tech Stack:** Python >=3.12, existing httpx/pydantic/cryptography stack (no new dependencies)

**Spec:** `docs/superpowers/specs/2026-04-06-dx-redesign.md`

---

## File Map

### New files
- Create: `ksef/result.py` — `InvoiceResult`, `TokenResult`, `LimitsInfo`, `SessionStatus` dataclasses
- Create: `ksef/easy.py` — `AsyncKSeF` class (the entire new public API)

### Rewritten files
- Modify: `ksef/__init__.py` — export `KSeF`, `AsyncKSeF`, `Environment` only
- Modify: `ksef/exceptions.py` — simplified hierarchy with better messages

### Consumer updates (batch)
- Modify: all `tests/unit/*.py` — update imports and test patterns
- Modify: all `tests/integration/*.py` — use new `AsyncKSeF` API
- Modify: all `examples/*.py` — use new `KSeF` / `AsyncKSeF` API
- Modify: `README.md` — complete rewrite
- Modify: `scripts/integration_test.py` — use new API

---

### Task 1: Result Types

**Files:**
- Create: `ksef/result.py`

- [ ] **Step 1: Create result dataclasses**

```python
"""Return types for the KSeF simplified API."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InvoiceResult:
    """Result of sending an invoice."""

    reference_number: str
    ksef_number: str | None = None
    status: str = "sent"


@dataclass
class TokenResult:
    """Result of creating a KSeF token."""

    reference_number: str
    token: str


@dataclass
class LimitsInfo:
    """Combined context, subject, and rate limits."""

    context: dict = field(default_factory=dict)
    subject: dict = field(default_factory=dict)
    rate: dict = field(default_factory=dict)


@dataclass
class SessionStatus:
    """Status of a KSeF session."""

    code: int
    description: str
    invoice_count: int | None = None
    successful_count: int | None = None
    failed_count: int | None = None
```

- [ ] **Step 2: Commit**

```bash
git add ksef/result.py
git commit -m "feat: add result dataclasses for simplified API"
```

---

### Task 2: Simplified Exceptions

**Files:**
- Modify: `ksef/exceptions.py`

- [ ] **Step 1: Rewrite exceptions with better messages and consolidated hierarchy**

```python
"""KSeF SDK exceptions with human-readable messages."""

from __future__ import annotations

from typing import Any


class KSeFError(Exception):
    """Base exception for all KSeF SDK errors."""


class KSeFAuthError(KSeFError):
    """Authentication failed."""

    def __init__(self, message: str, *, raw_response: dict | None = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response or {}


class KSeFInvoiceError(KSeFError):
    """Invoice validation or submission failed."""

    def __init__(self, message: str, *, details: list[str] | None = None, raw_response: dict | None = None) -> None:
        super().__init__(message)
        self.details = details or []
        self.raw_response = raw_response or {}


class KSeFPermissionError(KSeFError):
    """Insufficient permissions (403)."""

    def __init__(self, message: str, *, raw_response: dict | None = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response or {}


class KSeFRateLimitError(KSeFError):
    """Rate limited (429)."""

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class KSeFSessionError(KSeFError):
    """Session lifecycle error."""


class KSeFServerError(KSeFError):
    """Server-side error (5xx)."""

    def __init__(self, message: str, *, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


class KSeFTimeoutError(KSeFError):
    """Polling timeout."""


# --- Internal exceptions used by the low-level client layer ---
# These are caught by easy.py and re-raised as the public types above.

class _ApiError(Exception):
    """Internal: raw API error with status code and response body."""

    def __init__(self, message: str, status_code: int, body: dict | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body or {}
```

Note: The `BaseClient._handle_response` needs to be updated to raise `_ApiError` instead of the old exception types. The `easy.py` layer catches `_ApiError` and maps it to the correct public exception with a human-readable message. This is done in Task 3.

- [ ] **Step 2: Commit**

```bash
git add ksef/exceptions.py
git commit -m "feat: simplified exception hierarchy with better messages"
```

---

### Task 3: AsyncKSeF Core Implementation

**Files:**
- Create: `ksef/easy.py`

This is the largest task. `AsyncKSeF` wraps the entire internal stack.

- [ ] **Step 1: Create `ksef/easy.py` with full AsyncKSeF class**

The class must:
1. Accept constructor params (nip, token/cert+key, env, timeout)
2. Validate args on construction (ValueError for bad input)
3. Lazily authenticate on first API call
4. Manage crypto warmup internally
5. Implement all public methods from the spec
6. Map internal `_ApiError` to public exception types
7. Support `async with` context manager

Key internal flow for `send_invoice()`:
```
ensure_authenticated() → open online session → encrypt → send → close → brief poll for ksef_number → return InvoiceResult
```

Key internal flow for `session()` context:
```
ensure_authenticated() → warmup crypto → open online session → yield context → close on exit
```

The implementation delegates to existing coordinators/clients internally. It does NOT reimplement HTTP calls or crypto — it just orchestrates the existing pieces with a clean API surface.

Read the existing coordinator files for the exact method signatures:
- `ksef/coordinators/auth.py` — `AsyncAuthCoordinator`, `AuthSession`
- `ksef/coordinators/online_session.py` — `AsyncOnlineSessionManager`
- `ksef/coordinators/batch_session.py` — `AsyncBatchSessionManager`
- `ksef/coordinators/invoice_download.py` — `AsyncInvoiceDownloadManager`
- `ksef/client/__init__.py` — `AsyncKSeFClient`
- `ksef/crypto/service.py` — `CryptographyService`
- `ksef/crypto/qr.py` — `build_qr_code_1_url`

Also read `ksef/environments.py` for the `Environment` class.

The implementation should:
- Create `AsyncKSeFClient` internally
- Create `AsyncAuthCoordinator` internally
- Authenticate lazily via `_ensure_auth()`
- Cache `AuthSession` and `CryptographyService`
- Use `AsyncOnlineSessionManager` for invoice sending
- Use `AsyncBatchSessionManager` for batch sending
- Use `AsyncInvoiceDownloadManager` for downloads/exports
- Map all exceptions from the internal `_ApiError` to public types

Also update `ksef/client/base.py` to raise `_ApiError` instead of the old exception types (the old types no longer exist).

- [ ] **Step 2: Run tests to verify internal plumbing works**

Run: `uv run python -c "from ksef.easy import AsyncKSeF; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add ksef/easy.py ksef/client/base.py
git commit -m "feat: AsyncKSeF high-level API with lazy auth and automatic sessions"
```

---

### Task 4: Sync Wrapper & Package Init

**Files:**
- Modify: `ksef/__init__.py`

- [ ] **Step 1: Rewrite `__init__.py` to export new API only**

```python
"""KSeF Python SDK — Modern API for the Polish National e-Invoice System."""

from __future__ import annotations

from typing import Any

from ksef._sync import SyncWrapper
from ksef._version import __version__
from ksef.easy import AsyncKSeF
from ksef.environments import Environment
from ksef.result import InvoiceResult, LimitsInfo, SessionStatus, TokenResult


class KSeF:
    """Synchronous KSeF client.

    Usage::

        with KSeF(nip="1234567890", token="your-token", env="test") as client:
            result = client.send_invoice(xml_bytes)
    """

    def __init__(
        self,
        nip: str,
        *,
        token: str | None = None,
        cert: str | bytes | None = None,
        key: str | bytes | None = None,
        env: str | Environment = "production",
        timeout: float = 30.0,
    ) -> None:
        self._async = AsyncKSeF(nip=nip, token=token, cert=cert, key=key, env=env, timeout=timeout)
        self._wrapper = SyncWrapper(self._async)

    def __enter__(self) -> KSeF:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._wrapper.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapper, name)


__all__ = [
    "__version__",
    "AsyncKSeF",
    "Environment",
    "InvoiceResult",
    "KSeF",
    "LimitsInfo",
    "SessionStatus",
    "TokenResult",
]
```

- [ ] **Step 2: Verify imports**

Run: `uv run python -c "from ksef import KSeF, AsyncKSeF, Environment; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add ksef/__init__.py
git commit -m "feat: replace public API with KSeF/AsyncKSeF exports"
```

---

### Task 5: Update Unit Tests

**Files:**
- Modify: all files in `tests/unit/`

The unit tests currently test the internal low-level clients and coordinators directly. Since those modules are now internal (but still exist), the unit tests should still work with minimal changes — just import path updates where needed.

Key changes:
- Tests that import from `ksef` top-level (e.g., `from ksef import AsyncKSeFClient`) need to import from `ksef.client` instead
- Tests that import exceptions need the new exception types
- Add new unit tests for `ksef/easy.py` and `ksef/result.py`

- [ ] **Step 1: Fix imports across all unit test files**

Run `uv run pytest tests/unit/ -v` and fix any import errors. The internal modules still exist, so most tests just need `from ksef.client import AsyncKSeFClient` instead of `from ksef import AsyncKSeFClient`.

- [ ] **Step 2: Add unit tests for result types**

Create `tests/unit/test_result.py`:
```python
from ksef.result import InvoiceResult, LimitsInfo, SessionStatus, TokenResult


def test_invoice_result_defaults():
    r = InvoiceResult(reference_number="ref-1")
    assert r.reference_number == "ref-1"
    assert r.ksef_number is None
    assert r.status == "sent"


def test_token_result():
    r = TokenResult(reference_number="ref-1", token="tok-1")
    assert r.token == "tok-1"


def test_limits_info():
    r = LimitsInfo(context={"a": 1}, subject={"b": 2}, rate={"c": 3})
    assert r.context["a"] == 1


def test_session_status():
    r = SessionStatus(code=200, description="OK", invoice_count=5)
    assert r.invoice_count == 5
```

- [ ] **Step 3: Add unit tests for AsyncKSeF constructor validation**

Create `tests/unit/test_easy.py`:
```python
import pytest
from ksef.easy import AsyncKSeF


def test_requires_nip():
    with pytest.raises(TypeError):
        AsyncKSeF(token="tok")


def test_requires_auth_method():
    with pytest.raises(ValueError, match="token.*cert"):
        AsyncKSeF(nip="1234567890")


def test_rejects_both_token_and_cert():
    with pytest.raises(ValueError, match="token.*cert"):
        AsyncKSeF(nip="1234567890", token="tok", cert=b"cert", key=b"key")


def test_cert_requires_key():
    with pytest.raises(ValueError, match="key"):
        AsyncKSeF(nip="1234567890", cert=b"cert")


def test_valid_env_string():
    c = AsyncKSeF(nip="1234567890", token="tok", env="test")
    assert c._environment.name == "TEST"


def test_invalid_env_string():
    with pytest.raises(ValueError, match="env"):
        AsyncKSeF(nip="1234567890", token="tok", env="invalid")
```

- [ ] **Step 4: Run all unit tests**

Run: `uv run pytest tests/unit/ -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "feat: update unit tests for new API, add tests for result types and AsyncKSeF"
```

---

### Task 6: Update Integration Tests

**Files:**
- Modify: `tests/integration/conftest.py`
- Modify: all `tests/integration/test_*.py`

Integration tests should use the new `AsyncKSeF` API. The conftest fixtures change from `AsyncKSeFClient` + `AuthSession` to a single `AsyncKSeF` client.

- [ ] **Step 1: Rewrite `tests/integration/conftest.py`**

```python
"""Shared fixtures for integration tests against KSeF TEST environment."""

from __future__ import annotations

import os

import pytest
import pytest_asyncio

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(scope="session")
def nip() -> str:
    return os.environ.get("KSEF_TEST_NIP") or generate_random_nip()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client(nip):
    token = os.environ.get("KSEF_TEST_TOKEN")
    if token:
        c = AsyncKSeF(nip=nip, token=token, env="test")
    else:
        cert_pem, key_pem = generate_test_certificate(nip)
        c = AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test")
    async with c:
        yield c
```

- [ ] **Step 2: Update each integration test file to use `client: AsyncKSeF` directly**

Each test file changes from multi-fixture patterns (`client + auth_session + access_token`) to using the single `client: AsyncKSeF` fixture. For example:

```python
# Before:
async def test_get_challenge(client: AsyncKSeFClient):
    resp = await client.auth.get_challenge()

# After — test the public API, not internals:
async def test_send_and_check_status(client: AsyncKSeF):
    result = await client.send_invoice(generate_test_invoice_xml(nip))
    assert result.reference_number
```

The integration tests should test the PUBLIC API (`client.send_invoice`, `client.download_invoice`, etc.), not the internal low-level clients.

- [ ] **Step 3: Run integration tests**

Run: `uv run pytest tests/integration/ -m integration -v`

- [ ] **Step 4: Commit**

```bash
git add tests/integration/
git commit -m "feat: rewrite integration tests to use AsyncKSeF public API"
```

---

### Task 7: Update Examples

**Files:**
- Modify: all `examples/*.py`

Every example should use the new `KSeF`/`AsyncKSeF` API. The examples become dramatically simpler.

Key patterns:

```python
# Before (example 02):
from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
async with AsyncKSeFClient(environment=Environment.TEST) as client:
    auth = AsyncAuthCoordinator(client)
    session = await auth.authenticate_with_certificate(...)

# After:
from ksef import AsyncKSeF
async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
    # already authenticated on first use
```

```python
# Before (example 03):
crypto = await auth._get_or_create_crypto()
manager = AsyncOnlineSessionManager(client, session, crypto=crypto)
async with manager.open(schema_version="FA(3)") as online:
    result = await online.send_invoice_xml(xml_bytes)

# After:
result = await client.send_invoice(xml_bytes)
```

- [ ] **Step 1: Rewrite all 14 examples using new API**

- [ ] **Step 2: Run all examples to verify they work**

Run each: `uv run python examples/XX_name.py`

- [ ] **Step 3: Commit**

```bash
git add examples/
git commit -m "feat: rewrite all examples with simplified KSeF/AsyncKSeF API"
```

---

### Task 8: Rewrite README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite README with new API**

The README hero example becomes:

```python
from ksef import KSeF

with KSeF(nip="1234567890", token="your-token", env="test") as client:
    result = client.send_invoice(invoice_xml_bytes)
    print(result.ksef_number)
```

Cover: install, auth (token + cert), send invoice, download, batch, tokens, permissions, certs, limits, QR, testing, requirements.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README with simplified 3-line API"
```

---

### Task 9: Update Scripts & Final Verification

**Files:**
- Modify: `scripts/integration_test.py`

- [ ] **Step 1: Update integration test script to use new API**

- [ ] **Step 2: Run full verification**

```bash
uv run pytest tests/unit/ -v           # unit tests
uv run pytest tests/integration/ -m integration -v  # integration tests
uv run ruff check ksef/ tests/ examples/   # lint
uv run pyright ksef/ examples/             # type check
uv run python examples/02_authenticate_certificate.py  # smoke test
uv run python examples/03_send_invoice.py              # end-to-end
```

- [ ] **Step 3: Final commit**

```bash
git add scripts/ && git commit -m "chore: update scripts for new API"
```
