# ksef

Modern Python SDK for the Polish National e-Invoice System (KSeF) API 2.0.

```python
from ksef import KSeF

with KSeF(nip="1234567890", token="your-token", env="test") as client:
    result = client.send_invoice(invoice_xml_bytes)
    print(result.reference_number)
```

## Install

```sh
pip install ksef
```

With XAdES certificate auth:

```sh
pip install ksef[xades]
```

With QR code generation:

```sh
pip install ksef[qr]
```

Everything:

```sh
pip install ksef[all]
```

## Authentication

### KSeF Token

```python
from ksef import KSeF

with KSeF(nip="1234567890", token="your-ksef-token", env="production") as client:
    result = client.send_invoice(xml_bytes)
```

### Certificate (XAdES)

Requires `ksef[xades]`. The TEST environment accepts self-signed certificates.

```python
from ksef import AsyncKSeF

async with AsyncKSeF(nip="1234567890", cert=cert_pem, key=key_pem, env="test") as client:
    result = await client.send_invoice(xml_bytes)
```

### Lazy Authentication

Authentication happens automatically on first API call. No separate auth step needed.

## Sending Invoices

### Single Invoice

```python
from ksef import AsyncKSeF

async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
    result = await client.send_invoice(xml_bytes)
    print(result.reference_number)  # KSeF reference number
```

### Multiple Invoices (One-Shot)

```python
results = await client.send_invoices([xml1, xml2, xml3])
for r in results:
    print(r.reference_number)
```

### Interactive Session

For fine-grained control over a multi-invoice session:

```python
async with client.session() as s:
    await s.send(xml1)
    await s.send(xml2)
print(s.results)           # list of InvoiceResult
print(s.reference_number)  # session reference
```

## Downloading Invoices

```python
# Query metadata
metadata = await client.query_invoices(
    subjectType="subject1",
    dateRange={"dateType": "invoicing", "from": "2026-01-01T00:00:00", "to": "2026-03-31T23:59:59"},
)

# Download by KSeF number
xml_bytes = await client.download_invoice("1234567890-20260101-ABC123-DE")

# Bulk export
export_resp = await client.export_invoices(subjectType="subject1", dateRange={...})
```

## Token Management

```python
# Create
token_result = await client.create_token(
    permissions={"permissions": ["InvoiceRead", "InvoiceWrite"]},
    description="My API token",
)
print(token_result.token)

# List
tokens = await client.list_tokens()

# Revoke
await client.revoke_token(token_result.reference_number)
```

## Permissions

```python
# Query personal permissions
permissions = await client.query_permissions(pageSize=10, pageNumber=0)

# Check attachment (power of attorney) status
attachment = await client.get_attachment_status()
```

## Certificates

```python
# Check certificate limits
limits = await client.get_certificate_limits()

# Get enrollment data (DN attributes for CSR)
enrollment = await client.get_enrollment_data()
```

## Limits

Fetch context, subject, and rate limits in one call (parallel under the hood):

```python
limits = await client.get_limits()
print(limits.context)   # per-session limits
print(limits.subject)   # per-NIP limits
print(limits.rate)      # API throttling limits
```

## Session Status

```python
status = await client.get_session_status(reference_number)
print(status.code)
print(status.invoice_count)
print(status.successful_count)
```

## QR Codes

Generate verification QR codes for invoices:

```python
# URL only (no extra dependencies)
url = client.qr_url(invoice_date, seller_nip, file_sha256_b64url)

# QR image (requires ksef[qr])
from ksef.crypto.qr import generate_qr_code_1
image = generate_qr_code_1(Environment.PRODUCTION, invoice_date, seller_nip, file_hash)
```

## Sync vs Async

Both `KSeF` (sync) and `AsyncKSeF` (async) share the same API:

```python
# Async
from ksef import AsyncKSeF

async with AsyncKSeF(nip=nip, token=token, env="test") as client:
    result = await client.send_invoice(xml)

# Sync
from ksef import KSeF

with KSeF(nip=nip, token=token, env="test") as client:
    result = client.send_invoice(xml)
```

## Error Handling

All errors inherit from `KSeFError`:

```python
from ksef.exceptions import (
    KSeFError,            # base
    KSeFAuthError,        # 401
    KSeFInvoiceError,     # 400/450 on send
    KSeFPermissionError,  # 403
    KSeFRateLimitError,   # 429
    KSeFServerError,      # 5xx
    KSeFSessionError,     # session lifecycle
    KSeFTimeoutError,     # polling timeout
)

try:
    result = await client.send_invoice(xml)
except KSeFRateLimitError as exc:
    await asyncio.sleep(exc.retry_after or 30)
except KSeFAuthError:
    # re-authenticate
    pass
except KSeFError as exc:
    print(exc.raw_response)  # raw API response dict
```

## Testing Helpers

Generate valid test data for the TEST environment:

```python
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml

nip = generate_random_nip()                        # valid 10-digit NIP
cert_pem, key_pem = generate_test_certificate(nip)  # self-signed cert
invoice_xml = generate_test_invoice_xml(nip)         # minimal FA(3) XML
```

## Low-Level Client

For endpoints not exposed in the simplified API, access the internal client:

```python
async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
    await client._ensure_auth()
    token = await client._get_access_token()

    # All sub-clients available
    client._client.auth
    client._client.online
    client._client.batch
    client._client.invoices
    client._client.session_status
    client._client.sessions
    client._client.permissions
    client._client.certificates
    client._client.tokens
    client._client.limits
    client._client.peppol
    client._client.testdata
```

## Environments

```python
from ksef import Environment

Environment.TEST        # https://api-test.ksef.mf.gov.pl/v2
Environment.DEMO        # https://api-demo.ksef.mf.gov.pl/v2
Environment.PRODUCTION  # https://api.ksef.mf.gov.pl/v2
```

Or use strings: `"test"`, `"demo"`, `"production"` (or `"prod"`).

## Testing

```sh
# Unit tests
pytest

# Integration tests against KSeF TEST API (needs network)
pytest tests/integration/ -m integration -v

# With specific credentials
KSEF_TEST_NIP=1234567890 KSEF_TEST_TOKEN=abc pytest tests/integration/ -m integration -v
```

Integration tests generate a random NIP and self-signed certificate automatically. No pre-registration needed on the TEST environment.

## Supported Schema Versions

| Key          | System Code | Schema Version |
| ------------ | ----------- | -------------- |
| `FA(2)`      | FA (2)      | 1-0E           |
| `FA(3)`      | FA (3)      | 1-0E           |
| `FA_RR`      | FA_RR (1)   | 1-1E           |
| `PEF(3)`     | PEF (3)     | 2-1            |
| `PEF_KOR(3)` | PEF_KOR (3) | 2-1            |

## Examples

See [`examples/`](examples/) for 14 runnable scripts covering authentication, invoicing, batch sessions, token management, permissions, certificates, QR codes, error handling, and more. Every script runs against the TEST environment with zero setup:

```sh
uv run python examples/03_send_invoice.py
uv run python examples/05_batch_session.py
```

## Requirements

- Python >= 3.12
- httpx, pydantic >= 2, xsdata, cryptography (base)
- signxml (optional, for XAdES certificate auth)
- qrcode + Pillow (optional, for QR code generation)

## License

MIT
