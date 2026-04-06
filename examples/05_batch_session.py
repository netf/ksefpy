"""Send multiple invoices via a batch session using AsyncBatchSessionManager.

A batch session lets you upload many invoices in a single request as a
ZIP archive. KSeF processes them asynchronously. This is more efficient
than sending invoices one-by-one through online sessions when you have
large volumes.

Flow:
  1. Authenticate with certificate.
  2. Create a BatchSessionContext and add multiple invoice XMLs.
  3. Call manager.upload() — this builds the ZIP, encrypts it, and
     submits it to KSeF in one API call.
  4. Print the batch session reference number for status polling.

Run:
    uv run python examples/05_batch_session.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.coordinators.batch_session import AsyncBatchSessionManager
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

        # Step 3: Build a batch context and add multiple invoices.
        print(f"\nPreparing batch of {_INVOICE_COUNT} invoices ...")
        crypto = await auth._get_or_create_crypto()
        manager = AsyncBatchSessionManager(client, session, crypto=crypto)
        ctx = manager.new_context()

        for i in range(_INVOICE_COUNT):
            xml = generate_test_invoice_xml(nip)
            ctx.add_invoice_xml(xml)
            print(f"  Added invoice {i + 1} ({len(xml)} bytes)")

        print(f"  Total invoices in context: {ctx.invoice_count}")

        # Step 4: Upload the batch. The manager:
        #   - Packs all invoices into a ZIP archive.
        #   - Encrypts the ZIP with a freshly generated AES-256 session key.
        #   - Sends the encrypted ZIP and metadata to KSeF in one request.
        print("\nUploading batch ...")
        batch_resp = await manager.upload(ctx, schema_version="FA(3)")

        ref = batch_resp.get("referenceNumber") or batch_resp.get("reference_number", "")
        print("  Batch upload accepted.")
        print(f"  Batch reference number: {ref}")
        print(f"  Full response: {batch_resp}")
        print("\nThe batch is now processing asynchronously on KSeF.")
        print(f"Poll sessions/{ref} with your access token to check the result.")
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
