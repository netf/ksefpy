"""Request a bulk invoice export.

The export endpoint lets you download large sets of invoices as a ZIP
archive. The request is asynchronous: KSeF returns a reference number,
and you poll for status until the export is ready.

Run:
    uv run python examples/14_invoice_export.py

Requirements:
    pip install ksefpy[xades]
"""

from __future__ import annotations

import asyncio
import datetime

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml


async def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 2: Send a test invoice so there is data to export.
        print("\nSending a test invoice ...")
        invoice_xml = generate_test_invoice_xml(nip)
        result = await client.send_invoice(invoice_xml)
        print(f"  Invoice reference: {result.reference_number}")

        # Step 3: Request an export for today.
        today = datetime.date.today()
        print(f"\nRequesting export for date range: {today} ...")
        export_resp = await client.export_invoices(
            subjectType="subject1",
            dateRange={
                "dateType": "invoicing",
                "from": f"{today}T00:00:00",
                "to": f"{today}T23:59:59",
            },
        )
        ref = export_resp.get("referenceNumber") or export_resp.get("reference_number", "")
        print(f"  Export submitted.  Reference: {ref}")
        print(f"  Full response: {export_resp}")
        print("\nThe export is processing asynchronously on KSeF.")
        print(f"Poll the export status with reference {ref} to check results.")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
