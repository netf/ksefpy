"""Generate, list, and revoke KSeF API tokens.

KSeF tokens are long-lived credentials tied to a NIP. Typical usage:
  1. Bootstrap once with a certificate to create a long-lived token.
  2. Store the token value securely.
  3. Use the token for all subsequent authentication calls.

Run:
    uv run python examples/06_token_management.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 2: Generate a new KSeF token.
        print("\nGenerating token ...")
        result = await client.create_token(
            permissions={"permissions": ["InvoiceRead"]},
            description="Example read-only token",
        )
        print(f"  Token reference:        {result.reference_number}")
        print(f"  Token value (first 20): {result.token[:20]}...")

        # Step 3: List all tokens for this NIP.
        print("\nListing tokens ...")
        list_resp = await client.list_tokens()
        tokens = list_resp.get("tokens") or list_resp.get("items") or []
        print(f"  Total tokens on record: {len(tokens)}")
        for t in tokens:
            ref = t.get("referenceNumber", t.get("reference_number", "?"))
            desc = t.get("description", "")
            print(f"    - {ref}: {desc}")

        # Step 4: Revoke the token.
        print(f"\nRevoking token {result.reference_number} ...")
        await client.revoke_token(result.reference_number)
        print("  Token revoked successfully.")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
