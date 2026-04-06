"""Authenticate with a self-signed X.509 certificate against the KSeF TEST environment.

This is the "hello world" of the SDK. It requires no pre-existing credentials:
a valid Polish NIP and a matching self-signed certificate are generated on the fly.

Run:
    uv run python examples/02_authenticate_certificate.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Step 1: Generate a random valid Polish NIP and a matching self-signed certificate.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP:         {nip}")
    print(f"Certificate length:    {len(cert_pem)} bytes")

    # Step 2: Create an AsyncKSeF client with certificate auth.
    # Authentication happens lazily on first API call.
    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 3: Any API call triggers authentication automatically.
        # Here we fetch limits to prove the auth works.
        print("\nAuthenticating (lazily on first call) ...")
        limits = await client.get_limits()
        print("  Authentication successful!")
        print(f"  Context limits: {limits.context}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
