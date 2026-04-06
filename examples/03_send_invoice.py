"""Full invoice lifecycle: authenticate -> send invoice -> check status.

This is the most important example. It demonstrates the complete flow for
submitting a single e-invoice to KSeF.

Run:
    uv run python examples/03_send_invoice.py

Requirements:
    pip install ksefpy[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.testing import (
    generate_random_nip,
    generate_test_certificate,
    generate_test_invoice_xml,
)


async def main() -> None:
    # Step 1: Generate credentials -- no pre-registration needed on TEST.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    invoice_xml = generate_test_invoice_xml(nip)
    print(f"Generated NIP:          {nip}")
    print(f"Invoice XML size:       {len(invoice_xml)} bytes")

    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 2: Send the invoice. Authentication, session open/close, and
        # AES encryption are all handled automatically.
        print("\nSending invoice ...")
        result = await client.send_invoice(invoice_xml)
        print(f"  Invoice reference number: {result.reference_number}")
        print(f"  Status: {result.status}")
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
