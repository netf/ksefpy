"""Integration test against KSeF TEST environment.

Prerequisites:
  1. Generate a self-signed certificate (run this script with --generate-cert first)
  2. Create a test subject and grant permissions using the test data API

Usage:
  # Step 1: Generate a self-signed test certificate
  uv run python scripts/integration_test.py --generate-cert

  # Step 2: Create test subject + grant permissions + authenticate + send invoice
  uv run python scripts/integration_test.py --nip YOUR_TEST_NIP

  # Or with a KSeF token instead of certificate:
  uv run python scripts/integration_test.py --nip YOUR_TEST_NIP --token YOUR_KSEF_TOKEN
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("integration_test")

CERT_DIR = Path("test_certs")
CERT_PATH = CERT_DIR / "test_cert.pem"
KEY_PATH = CERT_DIR / "test_key.pem"


def generate_test_certificate() -> None:
    """Generate a self-signed certificate for KSeF TEST environment."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    CERT_DIR.mkdir(exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Organization"),
        x509.NameAttribute(NameOID.COMMON_NAME, "KSeF Test Certificate"),
        # NIP goes here as serialNumber for real certificates
        x509.NameAttribute(NameOID.SERIAL_NUMBER, "0000000000"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, key_encipherment=False, content_commitment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    KEY_PATH.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    CERT_PATH.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    logger.info("Certificate written to %s", CERT_PATH)
    logger.info("Private key written to %s", KEY_PATH)
    logger.info("Serial number (NIP placeholder): 0000000000")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Create a test subject on the KSeF TEST environment using the testdata API")
    logger.info("  2. Run: uv run python scripts/integration_test.py --nip <YOUR_TEST_NIP>")


async def run_integration_test(nip: str, token: str | None = None) -> None:
    """Run the full integration test flow."""
    from ksef import AsyncKSeFClient, Environment
    from ksef.coordinators.auth import AsyncAuthCoordinator
    from ksef.coordinators.online_session import AsyncOnlineSessionManager

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # === Step 1: Authenticate ===
        logger.info("=" * 60)
        logger.info("Step 1: Authenticating with KSeF TEST...")
        coordinator = AsyncAuthCoordinator(client)

        if token:
            logger.info("Using KSeF token authentication")
            session = await coordinator.authenticate_with_token(nip=nip, ksef_token=token)
        else:
            if not CERT_PATH.exists():
                logger.error("No certificate found. Run with --generate-cert first, or use --token.")
                sys.exit(1)
            logger.info("Using certificate authentication (XAdES)")
            cert_pem = CERT_PATH.read_bytes()
            key_pem = KEY_PATH.read_bytes()
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

        # Minimal FA(3) test invoice XML
        test_invoice_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="http://crd.gov.pl/wzor/2025/01/09/13064/">
  <Naglowek>
    <KodFormularza kodSystemowy="FA (3)" wersjaSchemy="1-0E">FA</KodFormularza>
    <WariantFormularza>2</WariantFormularza>
    <DataWytworzeniaFa>2026-04-06T10:00:00</DataWytworzeniaFa>
    <SystemInfo>ksef-python-sdk-test</SystemInfo>
  </Naglowek>
  <Podmiot1>
    <DaneIdentyfikacyjne>
      <NIP>{nip}</NIP>
      <Nazwa>Test Firma Sp. z o.o.</Nazwa>
    </DaneIdentyfikacyjne>
    <Adres>
      <KodKraju>PL</KodKraju>
      <AdresL1>ul. Testowa 1</AdresL1>
      <AdresL2>00-001 Warszawa</AdresL2>
    </Adres>
  </Podmiot1>
  <Podmiot2>
    <DaneIdentyfikacyjne>
      <NIP>9999999999</NIP>
      <Nazwa>Odbiorca Testowy</Nazwa>
    </DaneIdentyfikacyjne>
    <Adres>
      <KodKraju>PL</KodKraju>
      <AdresL1>ul. Odbiorcza 2</AdresL1>
      <AdresL2>00-002 Warszawa</AdresL2>
    </Adres>
  </Podmiot2>
  <Fa>
    <KodWaluty>PLN</KodWaluty>
    <P_1>2026-04-06</P_1>
    <P_2>TEST/2026/001</P_2>
    <P_6>2026-04-06</P_6>
    <P_13_1>1000.00</P_13_1>
    <P_14_1>230.00</P_14_1>
    <P_15>1230.00</P_15>
    <Adnotacje>
      <P_16>2</P_16>
      <P_17>2</P_17>
      <P_18>2</P_18>
      <P_18A>2</P_18A>
      <Zwolnienie>
        <P_19N>1</P_19N>
      </Zwolnienie>
      <NoweSrodkiTransportu>
        <P_22N>1</P_22N>
      </NoweSrodkiTransportu>
      <P_23>2</P_23>
      <PMarzy>
        <P_PMarzyN>1</P_PMarzyN>
      </PMarzy>
    </Adnotacje>
    <RodzajFaktury>VAT</RodzajFaktury>
    <FaWiersz>
      <NrWierszaFa>1</NrWierszaFa>
      <P_7>Usluga testowa</P_7>
      <P_8A>szt.</P_8A>
      <P_8B>1</P_8B>
      <P_9A>1000.00</P_9A>
      <P_11>1000.00</P_11>
      <P_12>23</P_12>
    </FaWiersz>
  </Fa>
</Faktura>""".strip()

        async with manager.open(schema_version="FA(3)") as online:
            logger.info("Session opened: %s", online.reference_number)
            result = await online.send_invoice_xml(test_invoice_xml.encode("utf-8"))
            logger.info("Invoice sent! Reference: %s", result.reference_number)

        logger.info("Session closed.")

        # === Step 3: Check session status ===
        logger.info("=" * 60)
        logger.info("Step 3: Checking session status...")
        await asyncio.sleep(2)  # brief wait for processing

        status = await client.session_status.get_session_status(
            online.reference_number, access_token=await session.get_access_token()
        )
        logger.info("Session status: %s", status.status)
        logger.info("Invoice count: %s", status.invoice_count)
        logger.info("Successful: %s", status.successful_invoice_count)
        logger.info("Failed: %s", status.failed_invoice_count)

        logger.info("=" * 60)
        logger.info("Integration test complete!")


def main() -> None:
    parser = argparse.ArgumentParser(description="KSeF SDK Integration Test")
    parser.add_argument("--generate-cert", action="store_true", help="Generate a self-signed test certificate")
    parser.add_argument("--nip", help="Test NIP to use for authentication")
    parser.add_argument("--token", help="KSeF token (alternative to certificate auth)")
    args = parser.parse_args()

    if args.generate_cert:
        generate_test_certificate()
        return

    if not args.nip:
        parser.print_help()
        print("\nError: --nip is required (or use --generate-cert)")
        sys.exit(1)

    asyncio.run(run_integration_test(nip=args.nip, token=args.token))


if __name__ == "__main__":
    main()
