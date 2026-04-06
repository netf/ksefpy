"""Send multiple invoices in a single session.

Demonstrates two approaches:
  1. send_invoices() -- one-shot batch, opens and closes the session automatically.
  2. session() context manager -- interactive session with individual sends.

Run:
    uv run python examples/05_batch_session.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.testing import (
    generate_random_nip,
    generate_test_certificate,
    generate_test_invoice_xml,
)

_INVOICE_COUNT = 3


async def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Approach 1: send_invoices() -- batch in one call.
        print(f"\nSending {_INVOICE_COUNT} invoices via send_invoices() ...")
        xmls = [generate_test_invoice_xml(nip) for _ in range(_INVOICE_COUNT)]
        results = await client.send_invoices(xmls)
        for i, r in enumerate(results, 1):
            print(f"  Invoice {i}: {r.reference_number}")

        # Approach 2: session() context manager -- interactive session.
        print(f"\nSending {_INVOICE_COUNT} invoices via session() context ...")
        async with client.session() as s:
            for i in range(_INVOICE_COUNT):
                xml = generate_test_invoice_xml(nip)
                result = await s.send(xml)
                print(f"  Invoice {i + 1}: {result.reference_number}")
        print(f"  Session reference: {s.reference_number}")
        print(f"  Total sent in session: {len(s.results)}")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
