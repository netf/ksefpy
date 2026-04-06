"""Authenticate with a KSeF API token against the TEST environment.

Because a KSeF token can only be obtained after first authenticating, this
example follows a two-step flow:
  1. Authenticate with a self-signed certificate to prove identity.
  2. Generate a new API token via the tokens endpoint.
  3. Authenticate a second time using that freshly generated token.

This mirrors what a real application would do: generate a long-lived token
during initial setup and then use it for all subsequent sessions.

Run:
    uv run python examples/01_authenticate_token.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.testing import generate_random_nip, generate_test_certificate


async def _authenticate_with_cert(client: AsyncKSeFClient, nip: str, cert_pem: bytes, key_pem: bytes):
    """Helper: authenticate via certificate and return an AuthSession."""
    auth = AsyncAuthCoordinator(client)
    return await auth.authenticate_with_certificate(
        nip=nip,
        certificate=cert_pem,
        private_key=key_pem,
    )


async def main() -> None:
    # Step 1: Generate a random NIP and self-signed certificate.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # Step 2: Authenticate with certificate to bootstrap the session.
        print("\nStep 1 — authenticating with certificate ...")
        cert_session = await _authenticate_with_cert(client, nip, cert_pem, key_pem)
        access_token = await cert_session.get_access_token()
        print("  Certificate auth successful.")

        # Step 3: Generate a new KSeF API token with InvoiceRead permission.
        print("\nStep 2 — generating a KSeF API token ...")
        token_resp = await client.tokens.generate(
            {
                "permissions": ["InvoiceRead"],
                "description": "Example token from 01_authenticate_token.py",
            },
            access_token=access_token,
        )
        ksef_token = token_resp.get("token") or token_resp.get("tokenValue")
        token_ref = token_resp.get("referenceNumber") or token_resp.get("reference_number", "")
        print(f"  Token reference: {token_ref}")
        print(f"  Token value (first 20 chars): {str(ksef_token)[:20]}...")

        # Step 4: Authenticate using the generated KSeF token.
        print("\nStep 3 — authenticating with KSeF token ...")
        auth = AsyncAuthCoordinator(client)
        token_session = await auth.authenticate_with_token(
            nip=nip,
            ksef_token=str(ksef_token),
        )
        new_access_token = await token_session.get_access_token()
        print("  Token auth successful!")
        print(f"  Access token (first 40 chars): {new_access_token[:40]}...")
        print(f"  Expires at: {token_session.access_token_info.valid_until}")

        # Step 5: Clean up — revoke the token we just created.
        print("\nStep 4 — revoking the generated token ...")
        if token_ref:
            await client.tokens.revoke(token_ref, access_token=access_token)
            print(f"  Token {token_ref} revoked.")
        else:
            print("  No referenceNumber returned — skipping revocation.")


if __name__ == "__main__":
    asyncio.run(main())
