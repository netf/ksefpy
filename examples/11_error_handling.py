"""Handle KSeF API errors gracefully with proper exception patterns.

The SDK raises typed exceptions for every failure mode:

  KSeFApiError          — base class for all HTTP-level API errors
  KSeFUnauthorizedError — HTTP 401 (bad token, wrong NIP, etc.)
  KSeFForbiddenError    — HTTP 403 (insufficient permissions)
  KSeFRateLimitError    — HTTP 429 (too many requests)
  KSeFServerError       — HTTP 5xx
  KSeFCryptoError       — local crypto failure (bad key, missing library, etc.)
  KSeFSessionError      — session lifecycle errors (already closed, etc.)
  KSeFTimeoutError      — polling timeout (auth, export, UPO)

This example demonstrates how to catch each type and what information
is available on each exception instance.

Run:
    uv run python examples/11_error_handling.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.coordinators.online_session import AsyncOnlineSessionManager
from ksef.exceptions import (
    KSeFApiError,
    KSeFCryptoError,
    KSeFRateLimitError,
    KSeFSessionError,
    KSeFTimeoutError,
    KSeFUnauthorizedError,
)
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml

# ---------------------------------------------------------------------------
# Helper: authenticate legitimately (used in later examples)
# ---------------------------------------------------------------------------

async def _authenticate(client: AsyncKSeFClient):
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    auth = AsyncAuthCoordinator(client)
    session = await auth.authenticate_with_certificate(
        nip=nip,
        certificate=cert_pem,
        private_key=key_pem,
    )
    return nip, session


# ---------------------------------------------------------------------------
# Scenario 1: Invalid token → KSeFUnauthorizedError
# ---------------------------------------------------------------------------

async def demo_unauthorized(client: AsyncKSeFClient) -> None:
    print("--- Scenario 1: KSeFUnauthorizedError (invalid token) ---")
    nip = generate_random_nip()
    auth = AsyncAuthCoordinator(client)
    try:
        await auth.authenticate_with_token(
            nip=nip,
            ksef_token="THIS-TOKEN-DOES-NOT-EXIST",
            poll_timeout=10.0,  # fail fast in this demo
        )
    except KSeFUnauthorizedError as exc:
        print(f"  Caught KSeFUnauthorizedError: {exc}")
        print(f"  HTTP status code: {exc.status_code}")
        print(f"  Problem details:  {exc.problem}")
    except KSeFApiError as exc:
        # Fallback: some TEST responses return a different error code.
        print(f"  Caught KSeFApiError (status {exc.status_code}): {exc}")
    except KSeFTimeoutError as exc:
        print(f"  Caught KSeFTimeoutError: {exc}")
    print()


# ---------------------------------------------------------------------------
# Scenario 2: Use an expired/bogus access token → KSeFUnauthorizedError
# ---------------------------------------------------------------------------

async def demo_bad_access_token(client: AsyncKSeFClient) -> None:
    print("--- Scenario 2: KSeFApiError (forged access token) ---")
    bogus_token = "eyJhbGciOiJSUzI1NiJ9.FAKE.SIGNATURE"
    try:
        await client.limits.get_context_limits(access_token=bogus_token)
    except KSeFUnauthorizedError as exc:
        print(f"  Caught KSeFUnauthorizedError: {exc}")
    except KSeFApiError as exc:
        print(f"  Caught KSeFApiError (status {exc.status_code}): {exc}")
    print()


# ---------------------------------------------------------------------------
# Scenario 3: Double-close an online session → KSeFSessionError
# ---------------------------------------------------------------------------

async def demo_session_error(client: AsyncKSeFClient) -> None:
    print("--- Scenario 3: KSeFSessionError (send after close) ---")
    nip, session = await _authenticate(client)
    invoice_xml = generate_test_invoice_xml(nip)
    auth_coord = AsyncAuthCoordinator(client)
    crypto = await auth_coord._get_or_create_crypto()
    manager = AsyncOnlineSessionManager(client, session, crypto=crypto)
    async with manager.open(schema_version="FA(3)") as online:
        # Send once successfully.
        await online.send_invoice_xml(invoice_xml)
        # Manually close so the session is marked as closed.
        await online.close()
        # Now try to send again — should raise KSeFSessionError.
        try:
            await online.send_invoice_xml(invoice_xml)
        except KSeFSessionError as exc:
            print(f"  Caught KSeFSessionError: {exc}")
    print()


# ---------------------------------------------------------------------------
# Scenario 4: Missing crypto dependency → KSeFCryptoError
# ---------------------------------------------------------------------------

async def demo_crypto_error() -> None:
    print("--- Scenario 4: KSeFCryptoError (missing optional dependency) ---")
    try:
        # generate_qr_code_1 raises KSeFCryptoError if qrcode isn't installed.
        import datetime as dt

        from ksef.crypto.qr import generate_qr_code_1

        nip = generate_random_nip()
        generate_qr_code_1(
            environment=Environment.TEST,
            invoice_date=dt.date.today(),
            seller_nip=nip,
            file_sha256_b64url="AAAA",
        )
        print("  qrcode is installed — no error raised.")
    except KSeFCryptoError as exc:
        print(f"  Caught KSeFCryptoError: {exc}")
    print()


# ---------------------------------------------------------------------------
# Scenario 5: Demonstrate KSeFRateLimitError attribute access pattern
# ---------------------------------------------------------------------------

async def demo_rate_limit_handling() -> None:
    print("--- Scenario 5: KSeFRateLimitError attribute pattern ---")
    # Simulate what you would do when catching a rate-limit error in production.
    exc = KSeFRateLimitError(
        message="Too many requests",
        retry_after=30.0,
        limit=100,
        remaining=0,
    )
    print(f"  Message:     {exc}")
    print(f"  retry_after: {exc.retry_after}s")
    print(f"  limit:       {exc.limit}")
    print(f"  remaining:   {exc.remaining}")
    print(f"  status_code: {exc.status_code}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        await demo_unauthorized(client)
        await demo_bad_access_token(client)
        await demo_session_error(client)

    await demo_crypto_error()
    await demo_rate_limit_handling()
    print("All error handling scenarios demonstrated.")


if __name__ == "__main__":
    asyncio.run(main())
