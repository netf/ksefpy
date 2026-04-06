"""Use the synchronous KSeF client -- no async/await required.

The KSeF class wraps AsyncKSeF on a private event loop, so it is safe
to use from regular synchronous code including scripts, Django views,
or Celery tasks.

Run:
    uv run python examples/10_sync_client.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

from ksef import KSeF
from ksef.testing import (
    generate_random_nip,
    generate_test_certificate,
    generate_test_invoice_xml,
)


def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    invoice_xml = generate_test_invoice_xml(nip)
    print(f"Generated NIP: {nip}")

    # Step 2: Use the sync KSeF client.
    with KSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 3: Send an invoice -- synchronous, no await needed.
        print("\nSending invoice (sync) ...")
        result = client.send_invoice(invoice_xml)
        print(f"  Invoice reference: {result.reference_number}")

        # Step 4: Fetch limits.
        print("\nFetching limits (sync) ...")
        limits = client.get_limits()
        print(f"  Context limits: {limits.context}")

    print("\nClient closed.  Done!")


if __name__ == "__main__":
    main()
