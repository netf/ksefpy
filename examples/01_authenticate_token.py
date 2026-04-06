"""Authenticate with a KSeF API token against the TEST environment.

This example bootstraps credentials by first authenticating with a
certificate, generating a token, and then using that token to create
a new AsyncKSeF client.

Run:
    uv run python examples/01_authenticate_token.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Step 1: Generate a random NIP and self-signed certificate.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    # Step 2: Authenticate with certificate and create a token.
    print("\nStep 1 -- authenticating with certificate ...")
    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        token_result = await client.create_token(
            permissions={"permissions": ["InvoiceRead", "InvoiceWrite"]},
            description="Example token from 01_authenticate_token.py",
        )
        print(f"  Token reference: {token_result.reference_number}")
        print(f"  Token value (first 20 chars): {token_result.token[:20]}...")

    # Step 3: Authenticate using the generated KSeF token.
    print("\nStep 2 -- authenticating with KSeF token ...")
    async with AsyncKSeF(nip=nip, token=token_result.token, env="test") as client:
        # Prove it works by listing tokens
        tokens = await client.list_tokens()
        print("  Token auth successful!")
        print(f"  Tokens on record: {len(tokens.get('tokens', []))}")

    # Step 4: Clean up -- revoke the token.
    print("\nStep 3 -- revoking the generated token ...")
    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        await client.revoke_token(token_result.reference_number)
        print(f"  Token {token_result.reference_number} revoked.")


if __name__ == "__main__":
    asyncio.run(main())
