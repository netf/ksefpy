"""Full invoice lifecycle: authenticate → open online session → send invoice → close → poll status.

This is the most important example. It demonstrates the complete flow for
submitting a single e-invoice to KSeF using an online (interactive) session:

  1. Generate NIP + certificate.
  2. Authenticate with the certificate.
  3. Open an online session (creates an AES-256 encrypted channel).
  4. Send a minimal FA(3) invoice XML.
  5. Close the session (happens automatically via context manager).
  6. Poll the session status to retrieve the KSeF reference number.

Run:
    uv run python examples/03_send_invoice.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.coordinators.online_session import AsyncOnlineSessionManager
from ksef.testing import (
    generate_random_nip,
    generate_test_certificate,
    generate_test_invoice_xml,
)


async def main() -> None:
    # Step 1: Generate credentials — no pre-registration needed on TEST.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    invoice_xml = generate_test_invoice_xml(nip)
    print(f"Generated NIP:          {nip}")
    print(f"Invoice XML size:       {len(invoice_xml)} bytes")

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # Step 2: Authenticate using the self-signed certificate.
        print("\nAuthenticating ...")
        auth = AsyncAuthCoordinator(client)
        session = await auth.authenticate_with_certificate(
            nip=nip,
            certificate=cert_pem,
            private_key=key_pem,
        )
        print("  Authentication successful.")

        # Step 3: Open an online session and send the invoice.
        # AsyncOnlineSessionManager handles AES key generation, encryption, and
        # session close automatically.
        manager = AsyncOnlineSessionManager(client, session)
        print("\nOpening online session ...")
        async with manager.open(schema_version="FA(3)") as online:
            session_ref = online.reference_number
            print(f"  Session reference: {session_ref}")

            # Step 4: Send the invoice XML. It is encrypted client-side before
            # transmission; KSeF decrypts it using the session AES key.
            print("\nSending invoice ...")
            result = await online.send_invoice_xml(invoice_xml)
            invoice_ref = result.reference_number
            print(f"  Invoice reference number: {invoice_ref}")
        # Session closes here automatically (context manager __aexit__).
        print("  Online session closed.")

        # Step 5: Poll the session status to see the processed invoices.
        print("\nPolling session status ...")
        access_token = await session.get_access_token()
        status = await client.session_status.get_session_status(
            session_ref, access_token=access_token
        )
        print(f"  Session status code:    {status.status_code}")
        print(f"  Invoices sent:          {status.invoice_count}")

        # Step 6: Retrieve per-invoice status to get the KSeF number.
        print("\nRetrieving invoice status ...")
        inv_status = await client.session_status.get_invoice_status(
            session_ref, invoice_ref, access_token=access_token
        )
        ksef_number = inv_status.get("ksefReferenceNumber") or inv_status.get("ksef_reference_number", "pending")
        print(f"  KSeF reference number:  {ksef_number}")
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
