"""Authenticate with a KSeF API token against the TEST environment.

This example bootstraps credentials by first authenticating with a
certificate, generating a token, and then using that token to create
a new AsyncKSeF client.

Run:
    uv run python examples/01_authenticate_token.py

Requirements:
    pip install ksef-python[xades]
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

    # Step 2: Authenticate with certificate, then generate and use a token.
    print("\nStep 1 -- authenticating with certificate ...")
    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Prove auth works by fetching limits
        limits = await client.get_limits()
        print(f"  Auth successful! Context limits: {limits.context}")

        # Step 3: Create a KSeF token.
        # Note: token creation requires CredentialsManage permission.
        # On the TEST env with a random NIP, this may return 403.
        print("\nStep 2 -- creating a KSeF token ...")
        try:
            token_result = await client.create_token(
                permissions=["InvoiceRead", "InvoiceWrite"],
                description="Example token from 01_authenticate_token.py",
            )
            print(f"  Token reference: {token_result.reference_number}")
            print(f"  Token value (first 20 chars): {token_result.token[:20]}...")
        except Exception as exc:
            print(f"  Token creation not available: {exc}")
            print("  (This is expected on TEST with some NIPs — Owner role doesn't always include CredentialsManage)")
            print("\nDone!")
            return

    # Step 4: Authenticate using the generated KSeF token.
    # The token has InvoiceRead + InvoiceWrite permissions, so we prove
    # it works by fetching limits (available to any authenticated user).
    print("\nStep 3 -- authenticating with KSeF token ...")
    async with AsyncKSeF(nip=nip, token=token_result.token, env="test") as client:
        limits = await client.get_limits()
        print("  Token auth successful!")
        print(f"  Rate limits available: {'rate' in dir(limits)}")

    # Step 5: Clean up -- revoke the token.
    print("\nStep 4 -- revoking the generated token ...")
    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        await client.revoke_token(token_result.reference_number)
        print(f"  Token {token_result.reference_number} revoked.")


if __name__ == "__main__":
    asyncio.run(main())
