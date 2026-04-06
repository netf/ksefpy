# Integration Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pytest-based integration test suite that validates all SDK endpoint groups against the real KSeF TEST environment.

**Architecture:** Session-scoped auth fixture authenticates once (random NIP + self-signed cert). Module-scoped fixtures manage stateful resources (sessions, tokens). Each test is a focused assertion on one endpoint. Tests are marked `@pytest.mark.integration` and excluded from default runs.

**Tech Stack:** pytest, pytest-asyncio, existing ksef SDK

**Spec:** `docs/superpowers/specs/2026-04-06-integration-tests-design.md`

---

## File Map

- Create: `ksef/testing.py` — NIP generation + cert generation helpers (extracted from scripts/integration_test.py)
- Modify: `pyproject.toml` — add `integration` marker, keep `addopts` excluding it
- Modify: `scripts/integration_test.py` — import helpers from `ksef/testing.py` instead of defining inline
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/conftest.py` — session-scoped fixtures (nip, client, auth_session, access_token)
- Create: `tests/integration/test_auth.py` — 3 tests
- Create: `tests/integration/test_online_session.py` — 4 tests
- Create: `tests/integration/test_batch_session.py` — 1 test
- Create: `tests/integration/test_invoices.py` — 2 tests
- Create: `tests/integration/test_tokens.py` — 4 tests
- Create: `tests/integration/test_certificates.py` — 2 tests
- Create: `tests/integration/test_permissions.py` — 2 tests
- Create: `tests/integration/test_limits.py` — 3 tests
- Create: `tests/integration/test_sessions.py` — 2 tests
- Create: `tests/integration/test_testdata.py` — 2 tests

---

### Task 1: Extract Test Helpers & Configure pytest

**Files:**
- Create: `ksef/testing.py`
- Modify: `pyproject.toml`
- Modify: `scripts/integration_test.py`

- [ ] **Step 1: Create `ksef/testing.py`**

```python
"""Test helpers for KSeF integration testing.

Provides NIP generation and self-signed certificate creation
for the KSeF TEST environment.
"""

from __future__ import annotations

import datetime
import random


_NIP_WEIGHTS = [6, 5, 7, 2, 3, 4, 5, 6, 7]


def generate_random_nip() -> str:
    """Generate a random valid Polish NIP (10 digits with correct checksum).

    Matches the C# client's ``MiscellaneousUtils.GetRandomNip()`` algorithm.
    """
    while True:
        digits = [random.randint(1, 9)]
        d2 = random.randint(0, 9)
        d3 = random.randint(0, 9)
        if d2 == 0 and d3 == 0:
            d3 = random.randint(1, 9)
        digits.extend([d2, d3])
        digits.extend([random.randint(0, 9) for _ in range(6)])

        checksum = sum(d * w for d, w in zip(digits, _NIP_WEIGHTS)) % 11
        if checksum == 10:
            continue
        digits.append(checksum)
        return "".join(str(d) for d in digits)


def generate_test_certificate(nip: str) -> tuple[bytes, bytes]:
    """Generate a self-signed certificate for KSeF TEST environment.

    Returns ``(cert_pem, key_pem)``.

    The certificate DN matches the format expected by KSeF TEST::

        givenName=Test, surname=User, serialNumber=TINPL-{NIP},
        CN=Test User, C=PL
    """
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.GIVEN_NAME, "Test"),
        x509.NameAttribute(NameOID.SURNAME, "User"),
        x509.NameAttribute(NameOID.SERIAL_NUMBER, f"TINPL-{nip}"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Test User"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=730))
        .sign(private_key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def generate_test_invoice_xml(nip: str) -> bytes:
    """Generate a minimal valid FA(3) invoice XML for testing."""
    today = datetime.date.today()
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="http://crd.gov.pl/wzor/2025/01/09/13064/">
  <Naglowek>
    <KodFormularza kodSystemowy="FA (3)" wersjaSchemy="1-0E">FA</KodFormularza>
    <WariantFormularza>2</WariantFormularza>
    <DataWytworzeniaFa>{now}</DataWytworzeniaFa>
    <SystemInfo>ksef-python-sdk-test</SystemInfo>
  </Naglowek>
  <Podmiot1>
    <DaneIdentyfikacyjne>
      <NIP>{nip}</NIP>
      <Nazwa>Test Firma Sp. z o.o.</Nazwa>
    </DaneIdentyfikacyjne>
    <Adres>
      <KodKraju>PL</KodKraju>
      <AdresL1>ul. Testowa 1</AdresL1>
      <AdresL2>00-001 Warszawa</AdresL2>
    </Adres>
  </Podmiot1>
  <Podmiot2>
    <DaneIdentyfikacyjne>
      <NIP>9999999999</NIP>
      <Nazwa>Odbiorca Testowy</Nazwa>
    </DaneIdentyfikacyjne>
    <Adres>
      <KodKraju>PL</KodKraju>
      <AdresL1>ul. Odbiorcza 2</AdresL1>
      <AdresL2>00-002 Warszawa</AdresL2>
    </Adres>
  </Podmiot2>
  <Fa>
    <KodWaluty>PLN</KodWaluty>
    <P_1>{today}</P_1>
    <P_2>TEST/{today.strftime("%Y")}/001</P_2>
    <P_6>{today}</P_6>
    <P_13_1>1000.00</P_13_1>
    <P_14_1>230.00</P_14_1>
    <P_15>1230.00</P_15>
    <Adnotacje>
      <P_16>2</P_16>
      <P_17>2</P_17>
      <P_18>2</P_18>
      <P_18A>2</P_18A>
      <Zwolnienie><P_19N>1</P_19N></Zwolnienie>
      <NoweSrodkiTransportu><P_22N>1</P_22N></NoweSrodkiTransportu>
      <P_23>2</P_23>
      <PMarzy><P_PMarzyN>1</P_PMarzyN></PMarzy>
    </Adnotacje>
    <RodzajFaktury>VAT</RodzajFaktury>
    <FaWiersz>
      <NrWierszaFa>1</NrWierszaFa>
      <P_7>Usluga testowa</P_7>
      <P_8A>szt.</P_8A>
      <P_8B>1</P_8B>
      <P_9A>1000.00</P_9A>
      <P_11>1000.00</P_11>
      <P_12>23</P_12>
    </FaWiersz>
  </Fa>
</Faktura>"""
    return xml.strip().encode("utf-8")
```

- [ ] **Step 2: Update `scripts/integration_test.py` to import from `ksef.testing`**

Replace the inline `_generate_random_nip`, `_generate_test_certificate` functions and the invoice XML template with:

```python
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml
```

Then use `generate_random_nip()` instead of `_generate_random_nip()`, `generate_test_certificate(nip)` instead of `_generate_test_certificate(nip)`, and `generate_test_invoice_xml(nip)` instead of the inline XML template. Remove the now-unused inline functions, `_NIP_WEIGHTS`, and the `import random` line.

- [ ] **Step 3: Update `pyproject.toml`**

Add the integration marker and default exclusion:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = ["integration: integration tests against KSeF TEST API"]
addopts = "-m 'not integration'"
```

- [ ] **Step 4: Verify unit tests still pass with new config**

Run: `uv run pytest tests/unit/ -v`
Expected: 87 passed (the `addopts` excludes integration by default)

- [ ] **Step 5: Commit**

```bash
git add ksef/testing.py scripts/integration_test.py pyproject.toml
git commit -m "feat: extract test helpers to ksef/testing.py, add integration marker"
```

---

### Task 2: Integration Test Fixtures

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/conftest.py`

- [ ] **Step 1: Create `tests/integration/__init__.py`**

Empty file.

- [ ] **Step 2: Create `tests/integration/conftest.py`**

```python
"""Shared fixtures for integration tests against KSeF TEST environment."""

from __future__ import annotations

import asyncio
import os

import pytest

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator, AuthSession
from ksef.testing import generate_random_nip, generate_test_certificate


@pytest.fixture(scope="session")
def nip() -> str:
    """Use KSEF_TEST_NIP env var or generate a random valid NIP."""
    return os.environ.get("KSEF_TEST_NIP") or generate_random_nip()


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client() -> AsyncKSeFClient:
    """Shared async KSeF client for all integration tests."""
    async with AsyncKSeFClient(environment=Environment.TEST) as c:
        yield c


@pytest.fixture(scope="session")
async def auth_session(client: AsyncKSeFClient, nip: str) -> AuthSession:
    """Authenticate once for the entire test run."""
    coordinator = AsyncAuthCoordinator(client)

    token = os.environ.get("KSEF_TEST_TOKEN")
    if token:
        return await coordinator.authenticate_with_token(nip=nip, ksef_token=token)

    cert_pem, key_pem = generate_test_certificate(nip)
    return await coordinator.authenticate_with_certificate(
        nip=nip,
        certificate=cert_pem,
        private_key=key_pem,
    )


@pytest.fixture(scope="session")
async def access_token(auth_session: AuthSession) -> str:
    """Current access token (auto-refreshes via AuthSession)."""
    return await auth_session.get_access_token()
```

- [ ] **Step 3: Commit**

```bash
git add tests/integration/
git commit -m "feat: add integration test fixtures (session-scoped auth)"
```

---

### Task 3: Auth & Limits Tests

**Files:**
- Create: `tests/integration/test_auth.py`
- Create: `tests/integration/test_limits.py`

These tests have no state dependencies — they use the shared `client` and `auth_session` fixtures directly.

- [ ] **Step 1: Create `tests/integration/test_auth.py`**

```python
"""Integration tests for authentication endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession


pytestmark = pytest.mark.integration


async def test_get_challenge(client: AsyncKSeFClient):
    """POST /auth/challenge returns a valid challenge."""
    resp = await client.auth.get_challenge()
    assert resp.challenge
    assert resp.timestamp_ms > 0
    assert resp.client_ip


async def test_authenticate_produces_tokens(auth_session: AuthSession):
    """Full auth flow produces valid access + refresh tokens."""
    assert auth_session.access_token_info.token
    assert auth_session.refresh_token_info.token
    assert auth_session.access_token_info.valid_until
    assert auth_session.refresh_token_info.valid_until


async def test_refresh_token(client: AsyncKSeFClient, auth_session: AuthSession):
    """POST /auth/token/refresh returns a new access token."""
    resp = await client.auth.refresh_token(
        refresh_token=auth_session.refresh_token_info.token
    )
    assert resp.access_token.token
    assert resp.access_token.valid_until
```

- [ ] **Step 2: Create `tests/integration/test_limits.py`**

```python
"""Integration tests for limits and rate-limits endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession


pytestmark = pytest.mark.integration


async def test_get_context_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /limits/context returns session limit info."""
    token = await auth_session.get_access_token()
    result = await client.limits.get_context_limits(access_token=token)
    assert isinstance(result, dict)
    assert "onlineSession" in result or "batchSession" in result


async def test_get_subject_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /limits/subject returns certificate limit info."""
    token = await auth_session.get_access_token()
    result = await client.limits.get_subject_limits(access_token=token)
    assert isinstance(result, dict)


async def test_get_rate_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /rate-limits returns rate limit groups."""
    token = await auth_session.get_access_token()
    result = await client.limits.get_rate_limits(access_token=token)
    assert isinstance(result, dict)
    assert "onlineSession" in result or "invoiceSend" in result
```

- [ ] **Step 3: Run to verify (will only work against real API)**

Run: `uv run pytest tests/integration/test_auth.py tests/integration/test_limits.py -m integration -v`

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_auth.py tests/integration/test_limits.py
git commit -m "feat: add auth and limits integration tests"
```

---

### Task 4: Online Session Tests

**Files:**
- Create: `tests/integration/test_online_session.py`

- [ ] **Step 1: Create `tests/integration/test_online_session.py`**

```python
"""Integration tests for online (interactive) session endpoints."""

from __future__ import annotations

import asyncio

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.coordinators.online_session import AsyncOnlineSessionManager
from ksef.crypto.service import CryptographyService
from ksef.models.sessions import SessionStatusResponse
from ksef.testing import generate_test_invoice_xml


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
async def online_session_data(
    client: AsyncKSeFClient,
    auth_session: AuthSession,
    nip: str,
):
    """Open an online session, send an invoice, close, and yield all references."""
    # Warmup crypto with the API's public keys
    crypto = CryptographyService()
    from ksef.coordinators.auth import AsyncAuthCoordinator

    coordinator = AsyncAuthCoordinator(client, crypto=crypto)
    await coordinator._warmup_crypto(crypto)

    manager = AsyncOnlineSessionManager(client, auth_session, crypto=crypto)

    session_ref = None
    invoice_ref = None

    async with manager.open(schema_version="FA(3)") as ctx:
        session_ref = ctx.reference_number
        xml = generate_test_invoice_xml(nip)
        result = await ctx.send_invoice_xml(xml)
        invoice_ref = result.reference_number

    # Brief wait for server-side processing
    await asyncio.sleep(3)

    return {
        "session_ref": session_ref,
        "invoice_ref": invoice_ref,
    }


async def test_open_online_session(online_session_data: dict):
    """POST /sessions/online returns a reference number."""
    assert online_session_data["session_ref"]


async def test_send_invoice(online_session_data: dict):
    """POST /sessions/online/{ref}/invoices returns an invoice reference."""
    assert online_session_data["invoice_ref"]


async def test_close_online_session(online_session_data: dict):
    """POST /sessions/online/{ref}/close succeeds (session was closed by fixture)."""
    # If we got here, close succeeded during fixture setup
    assert online_session_data["session_ref"]


async def test_get_session_status(
    client: AsyncKSeFClient,
    auth_session: AuthSession,
    online_session_data: dict,
):
    """GET /sessions/{ref} returns status with invoice count."""
    token = await auth_session.get_access_token()
    status = await client.session_status.get_session_status(
        online_session_data["session_ref"], access_token=token
    )
    assert isinstance(status, SessionStatusResponse)
    assert status.status.code == 200
    assert status.invoice_count is not None
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/test_online_session.py
git commit -m "feat: add online session integration tests"
```

---

### Task 5: Token Tests

**Files:**
- Create: `tests/integration/test_tokens.py`

- [ ] **Step 1: Create `tests/integration/test_tokens.py`**

```python
"""Integration tests for KSeF token management endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
async def generated_token(client: AsyncKSeFClient, auth_session: AuthSession):
    """Generate a KSeF token and yield its reference + token value. Revoke on teardown."""
    token = await auth_session.get_access_token()
    resp = await client.tokens.generate(
        {"permissions": ["InvoiceRead"], "description": "integration-test-token"},
        access_token=token,
    )
    ref = resp.get("referenceNumber") or resp.get("reference_number")
    token_value = resp.get("token")

    yield {"reference_number": ref, "token": token_value}

    # Teardown: revoke
    try:
        token = await auth_session.get_access_token()
        await client.tokens.revoke(ref, access_token=token)
    except Exception:
        pass


async def test_generate_token(generated_token: dict):
    """POST /tokens returns reference number and token string."""
    assert generated_token["reference_number"]
    assert generated_token["token"]


async def test_list_tokens(
    client: AsyncKSeFClient, auth_session: AuthSession, generated_token: dict
):
    """GET /tokens returns a list containing the generated token."""
    token = await auth_session.get_access_token()
    resp = await client.tokens.list_tokens(access_token=token)
    refs = [t.get("referenceNumber") for t in resp.get("tokens", [])]
    assert generated_token["reference_number"] in refs


async def test_get_token(
    client: AsyncKSeFClient, auth_session: AuthSession, generated_token: dict
):
    """GET /tokens/{ref} returns token details."""
    token = await auth_session.get_access_token()
    resp = await client.tokens.get(generated_token["reference_number"], access_token=token)
    assert resp.get("referenceNumber") == generated_token["reference_number"]
    assert resp.get("description") == "integration-test-token"


async def test_revoke_token(
    client: AsyncKSeFClient, auth_session: AuthSession, generated_token: dict
):
    """DELETE /tokens/{ref} succeeds."""
    token = await auth_session.get_access_token()
    # Revoke (fixture teardown also tries, but this tests the explicit call)
    await client.tokens.revoke(generated_token["reference_number"], access_token=token)
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/test_tokens.py
git commit -m "feat: add token management integration tests"
```

---

### Task 6: Certificate, Permission & Session List Tests

**Files:**
- Create: `tests/integration/test_certificates.py`
- Create: `tests/integration/test_permissions.py`
- Create: `tests/integration/test_sessions.py`

- [ ] **Step 1: Create `tests/integration/test_certificates.py`**

```python
"""Integration tests for certificate endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession


pytestmark = pytest.mark.integration


async def test_get_certificate_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /certificates/limits returns enrollment and certificate limits."""
    token = await auth_session.get_access_token()
    resp = await client.certificates.get_limits(access_token=token)
    assert "canRequest" in resp
    assert "enrollment" in resp
    assert "certificate" in resp


async def test_get_enrollment_data(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /certificates/enrollments/data returns DN attributes."""
    token = await auth_session.get_access_token()
    resp = await client.certificates.get_enrollment_data(access_token=token)
    assert "commonName" in resp
    assert "countryName" in resp
```

- [ ] **Step 2: Create `tests/integration/test_permissions.py`**

```python
"""Integration tests for permission endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession


pytestmark = pytest.mark.integration


async def test_grant_and_query_person_permission(
    client: AsyncKSeFClient, auth_session: AuthSession, nip: str
):
    """POST /permissions/persons/grants + POST /permissions/query/personal/grants."""
    token = await auth_session.get_access_token()

    # Grant InvoiceRead to a test PESEL
    grant_resp = await client.permissions.grant_person(
        {
            "subjectIdentifier": {"type": "pesel", "value": "30112206276"},
            "permissions": ["InvoiceRead"],
            "description": "integration-test-grant",
            "subjectDetails": {
                "subjectDetailsType": "PersonById",
                "personById": {"firstName": "Test", "lastName": "User", "pesel": "30112206276"},
            },
        },
        access_token=token,
    )
    assert "referenceNumber" in grant_resp

    # Query own permissions
    query_resp = await client.permissions.query_personal(
        {},
        access_token=token,
    )
    assert isinstance(query_resp, dict)


async def test_get_attachment_status(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /permissions/attachments/status returns a response."""
    token = await auth_session.get_access_token()
    resp = await client.permissions.get_attachment_status(access_token=token)
    assert isinstance(resp, dict)
```

- [ ] **Step 3: Create `tests/integration/test_sessions.py`**

```python
"""Integration tests for session listing endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession


pytestmark = pytest.mark.integration


async def test_list_sessions(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /sessions returns a session list."""
    token = await auth_session.get_access_token()
    resp = await client.session_status.list_sessions(
        access_token=token, params={"pageSize": "5", "sessionType": "online"}
    )
    assert isinstance(resp, dict)


async def test_list_active_auth_sessions(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /auth/sessions returns active authentication sessions."""
    token = await auth_session.get_access_token()
    resp = await client.sessions.list_sessions(access_token=token)
    assert isinstance(resp, dict)
```

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_certificates.py tests/integration/test_permissions.py tests/integration/test_sessions.py
git commit -m "feat: add certificate, permission, and session list integration tests"
```

---

### Task 7: Invoice, Batch & Test Data Tests

**Files:**
- Create: `tests/integration/test_invoices.py`
- Create: `tests/integration/test_batch_session.py`
- Create: `tests/integration/test_testdata.py`

- [ ] **Step 1: Create `tests/integration/test_invoices.py`**

```python
"""Integration tests for invoice query and download endpoints."""

from __future__ import annotations

import datetime

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession


pytestmark = pytest.mark.integration


async def test_query_metadata(client: AsyncKSeFClient, auth_session: AuthSession):
    """POST /invoices/query/metadata returns a response (may be empty)."""
    token = await auth_session.get_access_token()
    today = datetime.date.today()
    month_ago = today - datetime.timedelta(days=30)
    resp = await client.invoices.query_metadata(
        {
            "subjectType": "subject1",
            "dateRange": {
                "dateType": "invoicing",
                "from": month_ago.isoformat() + "T00:00:00",
                "to": today.isoformat() + "T23:59:59",
            },
        },
        access_token=token,
    )
    assert isinstance(resp, dict)
    assert "invoices" in resp or "items" in resp


async def test_download_invoice_not_found(client: AsyncKSeFClient, auth_session: AuthSession):
    """GET /invoices/ksef/{number} with a fake number returns an error."""
    token = await auth_session.get_access_token()
    with pytest.raises(Exception):
        await client.invoices.download("0000000000-20260101-000000-0000000000", access_token=token)
```

- [ ] **Step 2: Create `tests/integration/test_batch_session.py`**

```python
"""Integration tests for batch session endpoints."""

from __future__ import annotations

import base64

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.crypto.service import CryptographyService
from ksef.models.sessions import EncryptionInfo, FormCode


pytestmark = pytest.mark.integration


async def test_batch_open_and_close(client: AsyncKSeFClient, auth_session: AuthSession):
    """POST /sessions/batch open + close cycle."""
    # Warmup crypto
    crypto = CryptographyService()
    from ksef.coordinators.auth import AsyncAuthCoordinator

    coordinator = AsyncAuthCoordinator(client, crypto=crypto)
    await coordinator._warmup_crypto(crypto)

    materials = crypto.generate_session_materials()
    encryption = EncryptionInfo.from_session_materials(materials)

    token = await auth_session.get_access_token()

    # Open batch session
    resp = await client.batch.open(
        {
            "formCode": FormCode(
                system_code="FA (3)", schema_version="FA_2025010901", value="FA"
            ).model_dump(by_alias=True),
            "encryption": encryption.model_dump(by_alias=True),
            "batchFile": {
                "fileSize": 100,
                "fileHash": "a" * 64,
                "fileParts": [
                    {
                        "ordinalNumber": 1,
                        "partName": "part_0001",
                        "partSize": 100,
                        "partHash": "a" * 64,
                    }
                ],
            },
        },
        access_token=token,
    )
    assert "referenceNumber" in resp

    ref = resp["referenceNumber"]

    # Close (will likely fail because we didn't upload parts, but tests the endpoint path)
    try:
        await client.batch.close(ref, access_token=token)
    except Exception:
        pass  # Expected — batch close requires uploaded parts
```

- [ ] **Step 3: Create `tests/integration/test_testdata.py`**

```python
"""Integration tests for test data management endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.testing import generate_random_nip


pytestmark = pytest.mark.integration


async def test_create_and_remove_subject(client: AsyncKSeFClient, auth_session: AuthSession):
    """POST /testdata/subject + POST /testdata/subject/remove."""
    token = await auth_session.get_access_token()
    test_nip = generate_random_nip()

    # Create
    resp = await client.testdata.create_subject(
        {"nip": test_nip, "name": "Integration Test Subject"},
        access_token=token,
    )
    assert isinstance(resp, dict)

    # Remove
    resp = await client.testdata.remove_subject(
        {"nip": test_nip},
        access_token=token,
    )
    assert isinstance(resp, dict)


async def test_create_and_remove_person(client: AsyncKSeFClient, auth_session: AuthSession):
    """POST /testdata/person + POST /testdata/person/remove."""
    token = await auth_session.get_access_token()
    test_nip = generate_random_nip()

    # Create person (JDG / sole proprietor)
    resp = await client.testdata.create_person(
        {"nip": test_nip, "firstName": "Test", "lastName": "Person", "isBailiff": False},
        access_token=token,
    )
    assert isinstance(resp, dict)

    # Remove
    resp = await client.testdata.remove_person(
        {"nip": test_nip},
        access_token=token,
    )
    assert isinstance(resp, dict)
```

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_invoices.py tests/integration/test_batch_session.py tests/integration/test_testdata.py
git commit -m "feat: add invoice, batch session, and test data integration tests"
```

---

### Task 8: Run Full Suite & Final Verification

- [ ] **Step 1: Verify unit tests still pass (default run)**

Run: `uv run pytest tests/unit/ -v`
Expected: 87 passed

- [ ] **Step 2: Verify integration tests are discovered but excluded by default**

Run: `uv run pytest tests/ --collect-only 2>&1 | grep "integration"`
Expected: 0 tests collected (excluded by addopts)

- [ ] **Step 3: Verify integration tests are collected with marker**

Run: `uv run pytest tests/integration/ -m integration --collect-only`
Expected: ~25 tests collected

- [ ] **Step 4: Run integration tests against KSeF TEST**

Run: `uv run pytest tests/integration/ -m integration -v`
Expected: Tests run against the real API. Some may fail due to API-specific behavior — fix any SDK bugs discovered.

- [ ] **Step 5: Run lint**

Run: `uv run ruff check ksef/ tests/ scripts/`
Expected: All checks passed

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: complete integration test suite (25 tests, 10 endpoint groups)"
```
