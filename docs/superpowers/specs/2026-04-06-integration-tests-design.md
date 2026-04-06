# KSeF SDK Integration Tests — Design Specification

**Date**: 2026-04-06
**Status**: Approved

## Overview

Pytest-based integration test suite that runs against the KSeF TEST environment (`https://api-test.ksef.mf.gov.pl/v2`). Covers all 10 endpoint groups with ~25 happy-path tests. Runs separately from unit tests via a `--run-integration` marker.

## Constraints

- Tests never run by default — require `-m integration`
- Zero setup: random NIP + self-signed cert, no pre-registration needed
- Session-scoped auth fixture (one authentication per run)
- Env var overrides: `KSEF_TEST_NIP`, `KSEF_TEST_TOKEN`
- No retry logic for rate limits (25 tests won't hit the 100 req/s limit)

## Test Structure

```
tests/integration/
├── conftest.py              # Shared fixtures
├── test_auth.py             # Auth flow (3 tests)
├── test_online_session.py   # Online session lifecycle (4 tests)
├── test_batch_session.py    # Batch open/close (1 test)
├── test_invoices.py         # Query metadata, download (2 tests)
├── test_tokens.py           # Generate/list/get/revoke (4 tests)
├── test_certificates.py     # Limits, enrollment data (2 tests)
├── test_permissions.py      # Grant/query, attachment status (2 tests)
├── test_limits.py           # Context/subject/rate limits (3 tests)
├── test_sessions.py         # List sessions (2 tests)
└── test_testdata.py         # Create/remove subject+person (2 tests)
```

## Fixtures (`conftest.py`)

### Session-scoped (one per test run)

**`nip`** — `KSEF_TEST_NIP` env var or random valid NIP (10 digits, correct checksum).

**`client`** — `AsyncKSeFClient(environment=Environment.TEST)`. Shared httpx connection pool.

**`auth_session`** — Authenticates once:
- If `KSEF_TEST_TOKEN` is set: uses `AsyncAuthCoordinator.authenticate_with_token()`
- Otherwise: generates self-signed cert with DN `givenName=Test, surname=User, serialNumber=TINPL-{NIP}, CN=Test User, C=PL` and uses `AsyncAuthCoordinator.authenticate_with_certificate()`

**`access_token`** — Convenience shortcut: `await auth_session.get_access_token()`.

### Module-scoped (one per test file)

**`online_session_ref`** (in `test_online_session.py`) — Opens an online session, yields the reference number, closes on teardown.

**`generated_token_ref`** (in `test_tokens.py`) — Generates a KSeF token, yields the reference, revokes on teardown.

## Credential Generation

### Random NIP
Matches the C# client's `MiscellaneousUtils.GetRandomNip()`:
- First digit 1-9
- Digits 2-3: at least one non-zero
- Digits 4-9: random
- Digit 10: checksum using weights `[6, 5, 7, 2, 3, 4, 5, 6, 7]` mod 11 (retry if 10)

### Self-signed Certificate
Matches the C# client's `SelfSignedCertificateForSignatureBuilder`:
- RSA 2048-bit key
- DN: `givenName=Test, surname=User, serialNumber=TINPL-{NIP}, CN=Test User, C=PL`
- Valid from: now - 1 hour (matches C# `-61 minutes` pattern)
- Valid to: now + 2 years
- Signed with SHA-256

The TEST environment accepts self-signed certificates with any valid NIP — no pre-registration needed.

## Test Coverage Map

### test_auth.py (3 tests)
- `test_get_challenge` — POST /auth/challenge → verify challenge string + timestamp returned
- `test_authenticate_with_certificate` — full XAdES flow → verify access_token + refresh_token present
- `test_refresh_token` — POST /auth/token/refresh → verify new access_token returned

### test_online_session.py (4 tests)
Uses module-scoped fixture that opens a session and closes on teardown.
- `test_open_online_session` — POST /sessions/online → verify reference_number returned
- `test_send_invoice` — POST /sessions/online/{ref}/invoices → verify invoice reference returned
- `test_close_online_session` — POST /sessions/online/{ref}/close → verify no error
- `test_get_session_status` — GET /sessions/{ref} → verify status + invoice count

### test_batch_session.py (1 test)
- `test_batch_open_and_close` — POST /sessions/batch → POST close → verify no error

### test_invoices.py (2 tests)
- `test_query_metadata` — POST /invoices/query/metadata → verify response structure (may be empty list)
- `test_download_invoice` — GET /invoices/ksef/{number} → skip if no known KSeF number, otherwise verify XML bytes returned

### test_tokens.py (4 tests)
Uses module-scoped fixture that generates a token and revokes on teardown.
- `test_generate_token` — POST /tokens → verify reference_number + token string
- `test_list_tokens` — GET /tokens → verify list contains generated token
- `test_get_token` — GET /tokens/{ref} → verify token details
- `test_revoke_token` — DELETE /tokens/{ref} → verify no error

### test_certificates.py (2 tests)
- `test_get_certificate_limits` — GET /certificates/limits → verify can_request + enrollment/certificate limits
- `test_get_enrollment_data` — GET /certificates/enrollments/data → verify DN attributes returned

### test_permissions.py (2 tests)
- `test_grant_and_query_person_permission` — POST grant → POST query → verify permission exists
- `test_get_attachment_status` — GET /permissions/attachments/status → verify response

### test_limits.py (3 tests)
- `test_get_context_limits` — GET /limits/context → verify online_session/batch_session fields
- `test_get_subject_limits` — GET /limits/subject → verify enrollment/certificate fields
- `test_get_rate_limits` — GET /rate-limits → verify rate limit groups present

### test_sessions.py (2 tests)
- `test_list_sessions` — GET /sessions → verify response structure
- `test_list_active_auth_sessions` — GET /auth/sessions → verify current session appears

### test_testdata.py (2 tests)
- `test_create_and_remove_subject` — POST create → POST remove → verify no error
- `test_create_and_remove_person` — POST create → POST remove → verify no error

## Configuration

### pyproject.toml additions
```toml
[tool.pytest.ini_options]
markers = ["integration: integration tests against KSeF TEST API"]
addopts = "-m 'not integration'"
```

### Running
```bash
# Integration tests only
uv run pytest tests/integration/ -m integration -v

# With specific credentials
KSEF_TEST_NIP=1234567890 KSEF_TEST_TOKEN=abc uv run pytest tests/integration/ -m integration -v

# All tests (unit + integration)
uv run pytest -m "" tests/ -v
```

## Test Invoice XML

Minimal valid FA(3) invoice used in online session tests:
- Schema: `http://crd.gov.pl/wzor/2025/01/09/13064/`
- Seller: test NIP, "Test Firma Sp. z o.o."
- Buyer: NIP 9999999999, "Odbiorca Testowy"
- One line item: "Usluga testowa", 1000 PLN net + 23% VAT = 1230 PLN gross
- Dynamic dates (today)
