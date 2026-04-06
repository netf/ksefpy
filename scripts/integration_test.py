"""Integration test against KSeF TEST environment.

The TEST environment accepts self-signed certificates with any valid NIP.
No pre-registration is needed — just generate a random NIP and authenticate.

Usage:
  # Run with a random NIP (generates cert automatically):
  uv run python scripts/integration_test.py

  # Run with a specific NIP:
  uv run python scripts/integration_test.py --nip 1234567890

  # Run with a KSeF token instead of certificate:
  uv run python scripts/integration_test.py --nip 1234567890 --token YOUR_TOKEN
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("integration_test")


# ---------------------------------------------------------------------------
# Integration test flow
# ---------------------------------------------------------------------------

async def run_integration_test(nip: str, token: str | None = None) -> None:
    """Run the full integration test flow."""
    from ksef import AsyncKSeFClient, Environment
    from ksef.coordinators.auth import AsyncAuthCoordinator
    from ksef.coordinators.online_session import AsyncOnlineSessionManager

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # === Step 1: Authenticate ===
        logger.info("=" * 60)
        logger.info("Step 1: Authenticating with KSeF TEST...")
        logger.info("NIP: %s", nip)
        coordinator = AsyncAuthCoordinator(client)

        if token:
            logger.info("Using KSeF token authentication")
            session = await coordinator.authenticate_with_token(nip=nip, ksef_token=token)
        else:
            logger.info("Using self-signed certificate authentication (XAdES)")
            cert_pem, key_pem = generate_test_certificate(nip)
            session = await coordinator.authenticate_with_certificate(
                nip=nip,
                certificate=cert_pem,
                private_key=key_pem,
            )

        access_token = await session.get_access_token()
        logger.info("Authenticated! Access token: %s...", access_token[:20])

        # === Step 2: Open online session and send a test invoice ===
        logger.info("=" * 60)
        logger.info("Step 2: Opening online session...")

        manager = AsyncOnlineSessionManager(client, session)

        test_invoice_xml = generate_test_invoice_xml(nip)

        async with manager.open(schema_version="FA(3)") as online:
            logger.info("Session opened: %s", online.reference_number)
            result = await online.send_invoice_xml(test_invoice_xml)
            logger.info("Invoice sent! Reference: %s", result.reference_number)

        logger.info("Session closed.")

        # === Step 3: Check session status ===
        logger.info("=" * 60)
        logger.info("Step 3: Checking session status...")
        await asyncio.sleep(3)

        access_token = await session.get_access_token()
        status = await client.session_status.get_session_status(
            online.reference_number, access_token=access_token
        )
        logger.info("Session status: %s", status.status)
        logger.info("Invoice count: %s", status.invoice_count)
        logger.info("Successful: %s", status.successful_invoice_count)
        logger.info("Failed: %s", status.failed_invoice_count)

        logger.info("=" * 60)
        logger.info("Integration test complete!")


def main() -> None:
    parser = argparse.ArgumentParser(description="KSeF SDK Integration Test")
    parser.add_argument("--nip", help="NIP to use (random valid NIP generated if omitted)")
    parser.add_argument("--token", help="KSeF token (uses certificate auth if omitted)")
    args = parser.parse_args()

    nip = args.nip or generate_random_nip()

    if not args.nip:
        logger.info("Generated random NIP: %s", nip)

    asyncio.run(run_integration_test(nip=nip, token=args.token))


if __name__ == "__main__":
    main()
