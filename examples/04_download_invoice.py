"""Send an invoice then download it back by KSeF number.

Demonstrates:
  - Sending an invoice via a session (to get the session reference).
  - Polling the session for invoice status until a KSeF number is assigned.
  - Downloading raw invoice XML by its KSeF number.

Run:
    uv run python examples/04_download_invoice.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.exceptions import KSeFError
from ksef.testing import (
    generate_random_nip,
    generate_test_certificate,
    generate_test_invoice_xml,
)


async def main() -> None:
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    invoice_xml = generate_test_invoice_xml(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 1: Send an invoice inside a session so we get the session reference.
        print("\nSending invoice ...")
        async with client.session() as s:
            result = await s.send(invoice_xml)
            session_ref = s.reference_number
        print(f"  Invoice reference: {result.reference_number}")
        print(f"  Session reference: {session_ref}")

        # Step 2: Poll session status until the KSeF number is assigned.
        # The server processes invoices asynchronously after session close.
        print("\nWaiting for KSeF number ...")
        ksef_number = None
        for attempt in range(30):
            await asyncio.sleep(3)
            # Access the internal client to get per-invoice details
            await client._ensure_auth()
            token = await client._get_access_token()
            inv_status = await client._client.session_status.get_invoice_status(
                session_ref, result.reference_number, access_token=token,
            )
            ksef_number = inv_status.get("ksefNumber")
            if ksef_number:
                print(f"  KSeF number assigned: {ksef_number}")
                break
            print(f"  Not yet assigned (attempt {attempt + 1}/30) ...")
        else:
            print("  Timed out waiting for KSeF number.")
            print("\nDone!")
            return

        # Step 3: Download the invoice by its KSeF number.
        print(f"\nDownloading invoice {ksef_number} ...")
        for attempt in range(5):
            try:
                xml_bytes = await client.download_invoice(ksef_number)
                print(f"  Downloaded {len(xml_bytes)} bytes of XML.")
                snippet = xml_bytes[:200].decode("utf-8", errors="replace")
                print(f"  XML snippet:\n    {snippet}")
                break
            except KSeFError:
                print(f"  Not ready yet, retrying ({attempt + 1}/5) ...")
                await asyncio.sleep(3)

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
