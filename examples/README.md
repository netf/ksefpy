# KSeF SDK Examples

Runnable scripts demonstrating the KSeF Python SDK. All examples target the TEST environment and generate their own credentials -- no setup needed.

## Running

```sh
uv run python examples/03_send_invoice.py
```

## Examples

| # | Script | Description |
|---|--------|-------------|
| 01 | authenticate_token.py | Bootstrap a token via cert auth, then authenticate with it |
| 02 | authenticate_certificate.py | Authenticate with a self-signed certificate |
| 03 | send_invoice.py | Send a single invoice (full lifecycle) |
| 04 | download_invoice.py | Query invoice metadata and download by KSeF number |
| 05 | batch_session.py | Send multiple invoices (send_invoices + session context) |
| 06 | token_management.py | Generate, list, and revoke KSeF tokens |
| 07 | permissions.py | Query permissions and attachment status |
| 08 | certificates.py | Check certificate limits and generate CSRs |
| 09 | qr_codes.py | Generate QR code verification URLs and images |
| 10 | sync_client.py | Use the synchronous KSeF client |
| 11 | error_handling.py | Handle API errors with typed exceptions |
| 12 | test_data_setup.py | Create and remove test subjects/persons |
| 13 | limits_and_status.py | Query context, subject, and rate limits |
| 14 | invoice_export.py | Request bulk invoice export |

## Prerequisites

- `pip install ksef[all]` for all examples
- Or `pip install ksef[xades]` for certificate auth examples
- Or `pip install ksef[qr]` for QR code examples
