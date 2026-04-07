"""Handle KSeF API errors gracefully with proper exception patterns.

The SDK raises typed exceptions for every failure mode:

  KSeFError            -- base class for all KSeF errors
  KSeFAuthError        -- authentication failures (401)
  KSeFInvoiceError     -- invoice validation errors (400/450)
  KSeFPermissionError  -- permission denied (403)
  KSeFRateLimitError   -- rate limited (429)
  KSeFServerError      -- server errors (5xx)
  KSeFSessionError     -- session lifecycle errors
  KSeFTimeoutError     -- polling timeouts

Run:
    uv run python examples/11_error_handling.py

Requirements:
    pip install ksef-python[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.exceptions import (
    KSeFAuthError,
    KSeFError,
    KSeFInvoiceError,
    KSeFPermissionError,
    KSeFRateLimitError,
    KSeFServerError,
)
from ksef.testing import generate_random_nip, generate_test_certificate

# ---------------------------------------------------------------------------
# Scenario 1: Invalid token
# ---------------------------------------------------------------------------


async def demo_invalid_token() -> None:
    print("--- Scenario 1: KSeFAuthError (invalid token) ---")
    nip = generate_random_nip()
    try:
        async with AsyncKSeF(nip=nip, token="THIS-TOKEN-DOES-NOT-EXIST", env="test") as client:
            await client.get_limits()  # triggers auth
    except KSeFAuthError as exc:
        print(f"  Caught KSeFAuthError: {exc}")
    except KSeFError as exc:
        # Fallback: some TEST responses return a different error code.
        print(f"  Caught KSeFError: {exc}")
    print()


# ---------------------------------------------------------------------------
# Scenario 2: Download non-existent invoice
# ---------------------------------------------------------------------------


async def demo_not_found() -> None:
    print("--- Scenario 2: KSeFError (invoice not found) ---")
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    try:
        async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
            await client.download_invoice("0000000000-20260101-000000-0000000000")
    except KSeFError as exc:
        print(f"  Caught KSeFError: {exc}")
        print(f"  Raw response: {exc.raw_response}")
    print()


# ---------------------------------------------------------------------------
# Scenario 3: Demonstrate exception hierarchy
# ---------------------------------------------------------------------------


async def demo_exception_hierarchy() -> None:
    print("--- Scenario 3: Exception hierarchy ---")
    print(f"  KSeFAuthError is subclass of KSeFError: {issubclass(KSeFAuthError, KSeFError)}")
    print(f"  KSeFInvoiceError is subclass of KSeFError: {issubclass(KSeFInvoiceError, KSeFError)}")
    print(f"  KSeFPermissionError is subclass of KSeFError: {issubclass(KSeFPermissionError, KSeFError)}")
    print(f"  KSeFRateLimitError is subclass of KSeFError: {issubclass(KSeFRateLimitError, KSeFError)}")
    print(f"  KSeFServerError is subclass of KSeFError: {issubclass(KSeFServerError, KSeFError)}")
    print()

    # Show the pattern for handling rate limits
    print("  Recommended error handling pattern:")
    print("    try:")
    print("        result = await client.send_invoice(xml)")
    print("    except KSeFRateLimitError as exc:")
    print("        await asyncio.sleep(exc.retry_after or 30)")
    print("    except KSeFAuthError:")
    print("        # re-authenticate")
    print("    except KSeFError as exc:")
    print("        logging.error(f'KSeF error: {exc}')")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    await demo_invalid_token()
    await demo_not_found()
    await demo_exception_hierarchy()
    print("All error handling scenarios demonstrated.")


if __name__ == "__main__":
    asyncio.run(main())
