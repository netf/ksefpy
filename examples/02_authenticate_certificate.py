"""Authenticate with a self-signed X.509 certificate (XAdES) against the KSeF TEST environment.

This is the "hello world" of the SDK. It requires no pre-existing credentials:
a valid Polish NIP and a matching self-signed certificate are generated on the fly.

Run:
    uv run python examples/02_authenticate_certificate.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Step 1: Generate a random valid Polish NIP and a matching self-signed certificate.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP:         {nip}")
    print(f"Certificate length:    {len(cert_pem)} bytes")

    # Step 2: Open an async client targeting the TEST environment.
    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        auth = AsyncAuthCoordinator(client)

        # Step 3: Authenticate — KSeF TEST accepts any self-signed cert whose
        # serialNumber DN attribute is "TINPL-{NIP}".
        print("\nAuthenticating with certificate ...")
        session = await auth.authenticate_with_certificate(
            nip=nip,
            certificate=cert_pem,
            private_key=key_pem,
        )

        # Step 4: Retrieve the access token. AuthSession refreshes it automatically
        # before it expires, so always use get_access_token() rather than caching
        # the token string yourself.
        access_token = await session.get_access_token()
        print("Authentication successful!")
        print(f"Access token (first 40 chars): {access_token[:40]}...")
        print(f"Token expires at:              {session.access_token_info.valid_until}")


if __name__ == "__main__":
    asyncio.run(main())
