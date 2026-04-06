"""Send an invoice then download it back by KSeF number.

Demonstrates the AsyncInvoiceDownloadManager for:
  - Querying invoice metadata with a date/subject filter.
  - Downloading raw invoice XML by its KSeF reference number.

The example first sends an invoice (same flow as 03_send_invoice.py) to
guarantee there is at least one invoice in the session. It then waits for
the KSeF number to be assigned and downloads the XML.

Run:
    uv run python examples/04_download_invoice.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio
import datetime

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.coordinators.invoice_download import AsyncInvoiceDownloadManager
from ksef.coordinators.online_session import AsyncOnlineSessionManager
from ksef.testing import (
    generate_random_nip,
    generate_test_certificate,
    generate_test_invoice_xml,
)

_POLL_INTERVAL = 2.0
_POLL_TIMEOUT = 60.0


async def _wait_for_ksef_number(
    client: AsyncKSeFClient,
    session_ref: str,
    invoice_ref: str,
    access_token: str,
) -> str:
    """Poll invoice status until a KSeF reference number is assigned."""
    deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT
    while True:
        inv_status = await client.session_status.get_invoice_status(
            session_ref, invoice_ref, access_token=access_token
        )
        ksef_number = inv_status.get("ksefReferenceNumber") or inv_status.get("ksef_reference_number")
        if ksef_number:
            return ksef_number
        if asyncio.get_event_loop().time() >= deadline:
            raise TimeoutError(f"KSeF number not assigned after {_POLL_TIMEOUT}s")
        print("  Waiting for KSeF number ...")
        await asyncio.sleep(_POLL_INTERVAL)


async def main() -> None:
    # Step 1: Generate credentials and invoice XML.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    invoice_xml = generate_test_invoice_xml(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # Step 2: Authenticate.
        print("\nAuthenticating ...")
        auth = AsyncAuthCoordinator(client)
        session = await auth.authenticate_with_certificate(
            nip=nip,
            certificate=cert_pem,
            private_key=key_pem,
        )
        print("  Authentication successful.")

        # Step 3: Send an invoice to have something to download.
        print("\nSending invoice ...")
        manager = AsyncOnlineSessionManager(client, session)
        async with manager.open(schema_version="FA(3)") as online:
            session_ref = online.reference_number
            send_result = await online.send_invoice_xml(invoice_xml)
            invoice_ref = send_result.reference_number
            print(f"  Invoice reference: {invoice_ref}")

        # Step 4: Poll until the KSeF number is assigned.
        print("\nWaiting for KSeF number to be assigned ...")
        access_token = await session.get_access_token()
        ksef_number = await _wait_for_ksef_number(client, session_ref, invoice_ref, access_token)
        print(f"  KSeF number: {ksef_number}")

        # Step 5: Query invoice metadata using the download manager.
        print("\nQuerying invoice metadata ...")
        dl = AsyncInvoiceDownloadManager(client, session)
        today = datetime.date.today()
        metadata = await dl.query_metadata(
            {
                "subjectType": "subject1",
                "dateRange": {
                    "dateType": "invoicing",
                    "from": f"{today}T00:00:00",
                    "to": f"{today}T23:59:59",
                },
            }
        )
        count = metadata.get("count") or metadata.get("total", 0)
        print(f"  Invoices found in metadata query: {count}")

        # Step 6: Download the invoice XML by its KSeF number.
        print(f"\nDownloading invoice {ksef_number} ...")
        xml_bytes = await dl.download(ksef_number)
        print(f"  Downloaded {len(xml_bytes)} bytes of XML.")
        # Print a short snippet so we can see it's the right document.
        snippet = xml_bytes[:200].decode("utf-8", errors="replace")
        print(f"  XML snippet:\n    {snippet}")
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
