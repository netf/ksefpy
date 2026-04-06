# KSeF SDK Examples

Runnable scripts demonstrating the KSeF Python SDK. All examples target the TEST environment and generate their own credentials — no setup needed.

## Running

```sh
uv run python examples/02_authenticate_certificate.py
```

## Examples

| # | Script | Description |
|---|--------|-------------|
| 01 | authenticate_token.py | Authenticate with a KSeF token |
| 02 | authenticate_certificate.py | Authenticate with a self-signed certificate (XAdES) |
| 03 | send_invoice.py | Full lifecycle: auth → send invoice → check status |
| 04 | download_invoice.py | Query invoice metadata and download by KSeF number |
| 05 | batch_session.py | Send multiple invoices via batch session |
| 06 | token_management.py | Generate, list, get, and revoke KSeF tokens |
| 07 | permissions.py | Query permissions and attachment status |
| 08 | certificates.py | Check certificate limits and enrollment data |
| 09 | qr_codes.py | Generate QR code verification URLs |
| 10 | sync_client.py | Use the synchronous KSeFClient |
| 11 | error_handling.py | Handle API errors gracefully |
| 12 | test_data_setup.py | Create and remove test subjects/persons |
| 13 | limits_and_status.py | Query context, subject, and rate limits |
| 14 | invoice_export.py | Request bulk invoice export |

## Prerequisites

- `pip install ksef[all]` for all examples
- Or `pip install ksef[xades]` for certificate auth examples
- Or `pip install ksef[qr]` for QR code examples
