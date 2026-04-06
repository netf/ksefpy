"""Send an invoice then download it back by KSeF number.

Demonstrates:
  - Sending an invoice to have something to download.
  - Querying invoice metadata with a date filter.
  - Downloading raw invoice XML by its KSeF reference number.

Run:
    uv run python examples/04_download_invoice.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio
import datetime

from ksef import AsyncKSeF
from ksef.exceptions import KSeFError
from ksef.testing import (
    generate_random_nip,
    generate_test_certificate,
    generate_test_invoice_xml,
)

_POLL_INTERVAL = 3.0
_POLL_TIMEOUT = 90.0


async def main() -> None:
    # Step 1: Generate credentials and invoice XML.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    invoice_xml = generate_test_invoice_xml(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 2: Send an invoice.
        print("\nSending invoice ...")
        result = await client.send_invoice(invoice_xml)
        print(f"  Invoice reference: {result.reference_number}")

        # Step 3: Query invoice metadata.
        print("\nQuerying invoice metadata ...")
        today = datetime.date.today()
        metadata = await client.query_invoices(
            subjectType="subject1",
            dateRange={
                "dateType": "invoicing",
                "from": f"{today}T00:00:00",
                "to": f"{today}T23:59:59",
            },
        )
        count = metadata.get("count") or metadata.get("total", 0)
        print(f"  Invoices found: {count}")

        # Step 4: Download by KSeF number (once assigned).
        # In a real app you would poll session_status to get the ksef_number.
        # Here we show the download API with a retry loop.
        invoices = metadata.get("invoices", [])
        if invoices:
            ksef_number = invoices[0].get("ksefNumber")
            if ksef_number:
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
            else:
                print("  KSeF number not yet assigned.")
        else:
            print("  No invoices found in metadata query.")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
