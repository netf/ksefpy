# ksef-python

[![PyPI](https://img.shields.io/pypi/v/ksef-python.svg)](https://pypi.org/project/ksef-python/)
[![CI](https://github.com/netf/ksef-python/actions/workflows/ci.yml/badge.svg)](https://github.com/netf/ksef-python/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Modern Python SDK for the Polish National e-Invoice System (KSeF) API 2.0. Send invoices in 3 lines — authentication, encryption, and session management are handled automatically.

```python
from ksef import KSeF

with KSeF(nip="1234567890", token="your-token", env="test") as client:
    result = client.send_invoice(invoice_xml)
    print(result.reference_number)
```

## Features

- **Simple API** — one class, one method to send an invoice
- **Automatic auth** — lazy authentication on first API call, auto-refresh before expiry
- **Automatic encryption** — AES-256-CBC invoice encryption and RSA-OAEP key exchange handled internally
- **Full KSeF 2.0 coverage** — 78/78 API endpoints, all schema versions
- **Sync and async** — `KSeF` (sync) and `AsyncKSeF` (async) with identical API
- **Clean error handling** — typed exceptions with human-readable messages
- **Zero-setup testing** — generates random NIPs and self-signed certs for the TEST environment
- **14 runnable examples** — copy-paste and run against the TEST API

## Install

```sh
pip install ksef-python
```

With XAdES certificate authentication:

```sh
pip install ksef-python[xades]
```

With QR code generation:

```sh
pip install ksef-python[qr]
```

Everything:

```sh
pip install ksef-python[all]
```

## Quick Start

```python
import asyncio
from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml

async def main():
    # Generate test credentials (works on KSeF TEST — no registration needed)
    nip = generate_random_nip()
    cert, key = generate_test_certificate(nip)
    invoice_xml = generate_test_invoice_xml(nip)

    async with AsyncKSeF(nip=nip, cert=cert, key=key, env="test") as client:
        result = await client.send_invoice(invoice_xml)
        print(f"Invoice sent: {result.reference_number}")

asyncio.run(main())
```

## Authentication

### KSeF Token

```python
with KSeF(nip="1234567890", token="your-ksef-token") as client:
    result = client.send_invoice(xml)
```

### Certificate (XAdES)

Requires `ksef[xades]`. The TEST environment accepts self-signed certificates.

```python
async with AsyncKSeF(nip="1234567890", cert=cert_pem, key=key_pem, env="test") as client:
    result = await client.send_invoice(xml)
```

Authentication happens automatically on first API call — no separate auth step needed. Tokens are refreshed automatically before expiry.

## Sending Invoices

### Single Invoice

```python
result = await client.send_invoice(xml_bytes)
print(result.reference_number)
```

### Multiple Invoices (One-Shot)

Sends all invoices in a single session:

```python
results = await client.send_invoices([xml1, xml2, xml3])
for r in results:
    print(r.reference_number)
```

### Interactive Session

For fine-grained control:

```python
async with client.session() as s:
    await s.send(xml1)
    await s.send(xml2)
print(s.results)           # list of InvoiceResult
print(s.reference_number)  # session reference
```

## Downloading Invoices

```python
# Download by KSeF number
xml_bytes = await client.download_invoice("1234567890-20260101-ABC123-DE")

# Query metadata
metadata = await client.query_invoices(
    subjectType="subject1",
    dateRange={"dateType": "invoicing", "from": "2026-01-01T00:00:00", "to": "2026-03-31T23:59:59"},
)

# Bulk export (encryption handled automatically)
export = await client.export_invoices(
    subjectType="subject1",
    dateRange={"dateType": "invoicing", "from": "2026-01-01T00:00:00", "to": "2026-03-31T23:59:59"},
)
```

## Token Management

```python
# Create
token_result = await client.create_token(
    permissions=["InvoiceRead", "InvoiceWrite"],
    description="My automation token",
)
print(token_result.token)

# List and revoke
tokens = await client.list_tokens()
await client.revoke_token(token_result.reference_number)
```

## Other Operations

```python
# Permissions
permissions = await client.query_permissions()
attachment = await client.get_attachment_status()

# Certificates
limits = await client.get_certificate_limits()
enrollment = await client.get_enrollment_data()

# Limits (context + subject + rate in one call)
limits = await client.get_limits()
print(limits.context, limits.subject, limits.rate)

# Session status
status = await client.get_session_status(reference_number)
print(status.code, status.invoice_count)

# QR code verification URL
url = client.qr_url(invoice_date, seller_nip, file_sha256_b64url)
```

## Error Handling

All errors inherit from `KSeFError` with human-readable messages:

```python
from ksef.exceptions import KSeFError, KSeFAuthError, KSeFRateLimitError

try:
    result = await client.send_invoice(xml)
except KSeFRateLimitError as exc:
    print(f"Rate limited, retry after {exc.retry_after}s")
except KSeFAuthError:
    print("Authentication failed — check credentials")
except KSeFError as exc:
    print(f"KSeF error: {exc}")
    print(f"Raw response: {exc.raw_response}")
```

Exception hierarchy:

| Exception | When |
|-----------|------|
| `KSeFAuthError` | Authentication failures (401) |
| `KSeFInvoiceError` | Invoice validation errors (400/450) |
| `KSeFPermissionError` | Permission denied (403) |
| `KSeFRateLimitError` | Rate limited (429), includes `retry_after` |
| `KSeFServerError` | Server errors (5xx), includes `status_code` |
| `KSeFSessionError` | Session lifecycle errors |
| `KSeFTimeoutError` | Polling timeouts |

## Sync vs Async

Both `KSeF` (sync) and `AsyncKSeF` (async) share the same API:

```python
# Async
async with AsyncKSeF(nip=nip, token=token, env="test") as client:
    result = await client.send_invoice(xml)

# Sync
with KSeF(nip=nip, token=token, env="test") as client:
    result = client.send_invoice(xml)
```

> **Note:** `client.session()` is only available in async mode. For batch sending in sync mode, use `client.send_invoices([xml1, xml2])`.

## Testing

```sh
# Unit tests (131 tests)
uv run pytest

# Integration tests against real KSeF TEST API (28 tests)
uv run pytest tests/integration/ -m integration -v

# With specific credentials
KSEF_TEST_NIP=1234567890 KSEF_TEST_TOKEN=abc uv run pytest tests/integration/ -m integration -v
```

Integration tests generate a random NIP and self-signed certificate automatically — no pre-registration needed on the TEST environment.

### Test Helpers

```python
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml

nip = generate_random_nip()                         # valid 10-digit NIP with checksum
cert_pem, key_pem = generate_test_certificate(nip)  # self-signed cert for TEST env
invoice_xml = generate_test_invoice_xml(nip)         # minimal valid FA(3) invoice
```

## Advanced Usage

### Low-Level Client Access

For endpoints not exposed in the simplified API:

```python
async with AsyncKSeF(nip=nip, cert=cert, key=key, env="test") as client:
    await client._ensure_auth()
    token = await client._get_access_token()

    # Access any KSeF endpoint directly
    await client._client.testdata.create_subject({"subjectNip": nip, ...}, access_token=token)
    await client._client.sessions.list_sessions(access_token=token)
```

### Custom Environments

```python
from ksef import Environment

Environment.TEST        # https://api-test.ksef.mf.gov.pl/v2
Environment.DEMO        # https://api-demo.ksef.mf.gov.pl/v2
Environment.PRODUCTION  # https://api.ksef.mf.gov.pl/v2

# Or use strings: "test", "demo", "production" (or "prod")
```

## Supported Schema Versions

| Key | System Code | Schema Version |
|-----|-------------|----------------|
| `FA(2)` | FA (2) | 1-0E |
| `FA(3)` | FA (3) | 1-0E |
| `FA_RR` | FA_RR (1) | 1-1E |
| `PEF(3)` | PEF (3) | 2-1 |
| `PEF_KOR(3)` | PEF_KOR (3) | 2-1 |

## Examples

See [`examples/`](examples/) for 14 runnable scripts:

```sh
uv run python examples/03_send_invoice.py
uv run python examples/04_download_invoice.py
uv run python examples/05_batch_session.py
```

## Development

```sh
# Install dev dependencies
uv sync --dev --all-extras

# Run linter
uv run ruff check ksef/ tests/ examples/

# Run formatter
uv run ruff format ksef/ tests/ examples/

# Run type checker
uv run pyright ksef/

# Install pre-commit hooks
pre-commit install
```

## Requirements

- Python >= 3.12
- [httpx](https://www.python-httpx.org/) — async HTTP client
- [pydantic](https://docs.pydantic.dev/) >= 2 — data validation
- [xsdata](https://xsdata.readthedocs.io/) — XML schema bindings
- [cryptography](https://cryptography.io/) — AES, RSA, X.509
- [signxml](https://github.com/XML-Security/signxml) (optional) — XAdES signatures
- [qrcode](https://github.com/lincolnloop/python-qrcode) + [Pillow](https://pillow.readthedocs.io/) (optional) — QR code generation

## License

MIT
