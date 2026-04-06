#!/usr/bin/env python3
"""Quick integration smoke test using the high-level AsyncKSeF API.

Authenticates with a self-signed certificate, sends an invoice,
queries metadata, and fetches limits -- all in one script.

Usage:
    uv run python scripts/integration_test.py
    KSEF_TEST_NIP=1234567890 KSEF_TEST_TOKEN=abc uv run python scripts/integration_test.py
"""

from __future__ import annotations

import asyncio
import datetime
import os
import sys

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml


async def main() -> None:
    nip = os.environ.get("KSEF_TEST_NIP") or generate_random_nip()
    token = os.environ.get("KSEF_TEST_TOKEN")

    if token:
        print(f"Using token auth with NIP: {nip}")
        client = AsyncKSeF(nip=nip, token=token, env="test")
    else:
        cert_pem, key_pem = generate_test_certificate(nip)
        print(f"Using certificate auth with generated NIP: {nip}")
        client = AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test")

    async with client:
        # 1. Send a single invoice
        print("\n[1/5] Sending single invoice ...")
        invoice_xml = generate_test_invoice_xml(nip)
        result = await client.send_invoice(invoice_xml)
        print(f"  Reference: {result.reference_number}")
        assert result.reference_number, "send_invoice returned no reference"

        # 2. Send multiple invoices in one session
        print("\n[2/5] Sending batch of 2 invoices ...")
        xmls = [generate_test_invoice_xml(nip) for _ in range(2)]
        results = await client.send_invoices(xmls)
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"
        for i, r in enumerate(results, 1):
            print(f"  Invoice {i}: {r.reference_number}")

        # 3. Query invoice metadata
        print("\n[3/5] Querying invoice metadata ...")
        today = datetime.date.today()
        metadata = await client.query_invoices(
            subjectType="subject1",
            dateRange={
                "dateType": "invoicing",
                "from": f"{today}T00:00:00",
                "to": f"{today}T23:59:59",
            },
        )
        print(f"  Response keys: {list(metadata.keys())}")

        # 4. Fetch all limits
        print("\n[4/5] Fetching limits ...")
        limits = await client.get_limits()
        print(f"  Context: {limits.context}")
        print(f"  Subject: {limits.subject}")
        print(f"  Rate:    {limits.rate}")

        # 5. Token lifecycle
        print("\n[5/5] Token lifecycle (create + list + revoke) ...")
        token_result = await client.create_token(
            permissions={"permissions": ["InvoiceRead"]},
            description="integration-smoke-test",
        )
        print(f"  Created token: {token_result.reference_number}")
        tokens = await client.list_tokens()
        print(f"  Tokens listed: {len(tokens.get('tokens', []))}")
        await client.revoke_token(token_result.reference_number)
        print(f"  Token revoked: {token_result.reference_number}")

    print("\nAll smoke tests passed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
