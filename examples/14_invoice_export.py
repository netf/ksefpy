"""Request a bulk invoice export and poll until completion.

The export endpoint lets you download large sets of invoices as a ZIP
archive. The request is asynchronous: KSeF returns a reference number,
and you poll for status until the export is ready.

This example demonstrates:
  - Submitting an export request for a date range.
  - Polling for the export status until completion (or timeout).
  - Alternatively using export_and_wait() for automatic polling.

If no invoices match the date range the export will still succeed but
produce an empty archive — that is normal on a freshly created NIP.

Run:
    uv run python examples/14_invoice_export.py

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
from ksef.exceptions import KSeFTimeoutError
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml


async def _send_invoice(client: AsyncKSeFClient, session, nip: str) -> None:
    """Send one invoice so the export has something to find."""
    invoice_xml = generate_test_invoice_xml(nip)
    manager = AsyncOnlineSessionManager(client, session)
    async with manager.open(schema_version="FA(3)") as online:
        result = await online.send_invoice_xml(invoice_xml)
        print(f"  Invoice reference: {result.reference_number}")


async def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
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

        # Step 3: Send a test invoice so there is data to export.
        print("\nSending a test invoice ...")
        await _send_invoice(client, session, nip)
        print("  Invoice sent.")

        # Step 4: Build an export request for today.
        today = datetime.date.today()
        export_request = {
            "subjectType": "subject1",
            "dateRange": {
                "dateType": "invoicing",
                "from": f"{today}T00:00:00",
                "to": f"{today}T23:59:59",
            },
        }
        print(f"\nRequesting export for date range: {today} → {today}")

        dl = AsyncInvoiceDownloadManager(client, session)

        # Step 5a: Manual approach — submit the request and get a reference number.
        export_resp = await dl.export(export_request)
        ref = export_resp.get("referenceNumber") or export_resp.get("reference_number", "")
        print(f"  Export submitted.  Reference: {ref}")

        # Step 5b: Poll until the export finishes (or times out).
        # In practice use export_and_wait() for convenience.
        if ref:
            print("\nPolling export status (manual) ...")
            for attempt in range(1, 11):
                status = await dl.get_export_status(ref)
                code = (status.get("status") or {}).get("code")
                print(f"  Attempt {attempt}: status code = {code}")
                if str(code) == "200":
                    print("  Export complete!")
                    print(f"  Final status: {status}")
                    break
                await asyncio.sleep(3)
            else:
                print("  Export did not complete within 10 polls — try export_and_wait() for auto-retry.")

        # Step 5c: Convenience method — automatic polling with configurable timeout.
        print("\nUsing export_and_wait() (automatic polling) ...")
        try:
            final = await dl.export_and_wait(
                export_request,
                poll_interval=3.0,
                poll_timeout=60.0,
            )
            print(f"  export_and_wait completed.  Final status: {final}")
        except KSeFTimeoutError as exc:
            print(f"  export_and_wait timed out: {exc}")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
