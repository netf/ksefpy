"""Generate, list, retrieve, and revoke KSeF API tokens.

KSeF tokens are long-lived credentials tied to a NIP. They can carry a
specific set of permissions (e.g. InvoiceRead, InvoiceWrite). Typical usage:

  1. Bootstrap once with a certificate to create a long-lived token.
  2. Store the token value securely.
  3. Use the token for all subsequent authentication calls.

This example demonstrates the full token lifecycle using the low-level
client.tokens sub-client.

Run:
    uv run python examples/06_token_management.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # Step 2: Authenticate with certificate.
        print("\nAuthenticating ...")
        auth = AsyncAuthCoordinator(client)
        session = await auth.authenticate_with_certificate(
            nip=nip,
            certificate=cert_pem,
            private_key=key_pem,
        )
        access_token = await session.get_access_token()
        print("  Authentication successful.")

        # Step 3: Generate a new KSeF token with InvoiceRead permission.
        # The 'permissions' list controls what the token bearer can do.
        print("\nGenerating token ...")
        token_resp = await client.tokens.generate(
            {
                "permissions": ["InvoiceRead"],
                "description": "Example read-only token",
            },
            access_token=access_token,
        )
        token_ref = token_resp.get("referenceNumber") or token_resp.get("reference_number", "")
        token_value = token_resp.get("token") or token_resp.get("tokenValue", "")
        print(f"  Token reference:           {token_ref}")
        print(f"  Token value (first 20):    {str(token_value)[:20]}...")

        # Step 4: List all tokens for this NIP.
        print("\nListing tokens ...")
        list_resp = await client.tokens.list_tokens(access_token=access_token)
        tokens = list_resp.get("tokens") or list_resp.get("items") or []
        print(f"  Total tokens on record: {len(tokens)}")
        for t in tokens:
            print(f"    - {t.get('referenceNumber', t.get('reference_number', '?'))}: {t.get('description', '')}")

        # Step 5: Get details for the token we just created.
        if token_ref:
            print(f"\nGetting token details for {token_ref} ...")
            details = await client.tokens.get(token_ref, access_token=access_token)
            print(f"  Permissions: {details.get('permissions', [])}")
            print(f"  Description: {details.get('description', '')}")
            print(f"  Created at:  {details.get('createdAt') or details.get('created_at', 'unknown')}")

        # Step 6: Revoke the token.
        if token_ref:
            print(f"\nRevoking token {token_ref} ...")
            await client.tokens.revoke(token_ref, access_token=access_token)
            print("  Token revoked successfully.")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
