# ksef

Modern Python SDK for the Polish National e-Invoice System (KSeF) API 2.0.

```python
from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.coordinators.online_session import AsyncOnlineSessionManager

async with AsyncKSeFClient(environment=Environment.TEST) as client:
    # Authenticate
    auth = AsyncAuthCoordinator(client)
    session = await auth.authenticate_with_token(nip="1234567890", ksef_token="your-token")

    # Send an invoice
    manager = AsyncOnlineSessionManager(client, session)
    async with manager.open(schema_version="FA(3)") as online:
        result = await online.send_invoice_xml(invoice_xml_bytes)
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
from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator

async with AsyncKSeFClient(environment=Environment.PRODUCTION) as client:
    auth = AsyncAuthCoordinator(client)
    session = await auth.authenticate_with_token(
        nip="1234567890",
        ksef_token="your-ksef-token",
    )
    token = await session.get_access_token()
```

### Certificate (XAdES)

Requires `ksef[xades]`. The TEST environment accepts self-signed certificates.

```python
session = await auth.authenticate_with_certificate(
    nip="1234567890",
    certificate_path="/path/to/cert.pem",
    private_key_path="/path/to/key.pem",
)
```

### Token Auto-Refresh

`AuthSession` refreshes the access token automatically before expiry:

```python
token = await session.get_access_token()  # always returns a valid token
```

## Sending Invoices

### Online Session (Interactive)

```python
from ksef.coordinators.online_session import AsyncOnlineSessionManager

manager = AsyncOnlineSessionManager(client, session)

async with manager.open(schema_version="FA(3)") as online:
    # From raw XML bytes
    result = await online.send_invoice_xml(xml_bytes)

    # From an xsdata model
    result = await online.send_invoice(invoice_obj)

    print(result.reference_number)
# Session closes automatically
```

### Batch Session

```python
from ksef.coordinators.batch_session import AsyncBatchSessionManager

manager = AsyncBatchSessionManager(client, session)
ctx = manager.new_context()
ctx.add_invoice_xml(invoice1_bytes)
ctx.add_invoice_xml(invoice2_bytes)
resp = await manager.upload(ctx, schema_version="FA(3)")
```

## Downloading Invoices

```python
from ksef.coordinators.invoice_download import AsyncInvoiceDownloadManager

dl = AsyncInvoiceDownloadManager(client, session)

# Query metadata
metadata = await dl.query_metadata({
    "subjectType": "subject1",
    "dateRange": {"dateType": "invoicing", "from": "2026-01-01T00:00:00", "to": "2026-03-31T23:59:59"},
})

# Download by KSeF number
xml_bytes = await dl.download("1234567890-20260101-ABC123-DE")
```

## Sync Client

Every async operation has a sync equivalent:

```python
from ksef import KSeFClient, Environment

with KSeFClient(environment=Environment.TEST) as client:
    challenge = client.auth.get_challenge()
```

## Low-Level Client

Access any endpoint directly:

```python
async with AsyncKSeFClient(environment=Environment.TEST) as client:
    # All sub-clients available
    client.auth          # challenge, token auth, xades auth, refresh
    client.online        # open, send invoice, close
    client.batch         # open, upload part, close
    client.invoices      # download, query metadata, export
    client.session_status  # session status, invoices, UPO
    client.sessions      # list/invalidate active auth sessions
    client.permissions   # grant, revoke, query
    client.certificates  # limits, enroll, retrieve, revoke, query
    client.tokens        # generate, list, get, revoke
    client.limits        # context, subject, rate limits
    client.peppol        # query providers
    client.testdata      # create/remove test subjects and persons
```

## Environments

```python
from ksef import Environment

Environment.TEST        # https://api-test.ksef.mf.gov.pl/v2
Environment.DEMO        # https://api-demo.ksef.mf.gov.pl/v2
Environment.PRODUCTION  # https://api.ksef.mf.gov.pl/v2
```

## Cryptography

AES-256-CBC encryption, RSA-OAEP key encryption, and XAdES signing are handled automatically by the coordinators. For advanced use:

```python
from ksef.crypto.service import CryptographyService

crypto = CryptographyService()
materials = crypto.generate_session_materials()  # AES key + IV + RSA-encrypted key
encrypted = crypto.encrypt_aes256(plaintext, materials.key, materials.iv)
```

## QR Codes

Generate verification QR codes for invoices. Requires `ksef[qr]`.

```python
from ksef.crypto.qr import build_qr_code_1_url, generate_qr_code_1

# URL only
url = build_qr_code_1_url(Environment.PRODUCTION, invoice_date, seller_nip, file_sha256_b64url)

# QR image
image = generate_qr_code_1(Environment.PRODUCTION, invoice_date, seller_nip, file_sha256_b64url)
```

## Testing

```sh
# Unit tests (87 tests, runs by default)
pytest

# Integration tests against KSeF TEST API (29 tests, needs network)
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
uv run python examples/02_authenticate_certificate.py
uv run python examples/03_send_invoice.py
```

## Requirements

- Python >= 3.12
- httpx, pydantic >= 2, xsdata, cryptography (base)
- signxml (optional, for XAdES certificate auth)
- qrcode + Pillow (optional, for QR code generation)

## License

MIT
