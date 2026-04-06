"""Public test helpers for KSeF integration tests.

Provides utilities for generating valid Polish NIPs, self-signed certificates,
and minimal FA(3) invoice XML suitable for use against the KSeF TEST environment.
"""

from __future__ import annotations

import datetime
import random

__all__ = [
    "generate_random_nip",
    "generate_test_certificate",
    "generate_test_invoice_xml",
]

_NIP_WEIGHTS = [6, 5, 7, 2, 3, 4, 5, 6, 7]


def generate_random_nip() -> str:
    """Generate a random valid Polish NIP (10 digits with correct checksum)."""
    while True:
        digits = [random.randint(1, 9)]  # first digit 1-9
        # second and third: at least one must be non-zero
        d2 = random.randint(0, 9)
        d3 = random.randint(0, 9)
        if d2 == 0 and d3 == 0:
            d3 = random.randint(1, 9)
        digits.extend([d2, d3])
        digits.extend([random.randint(0, 9) for _ in range(6)])

        checksum = sum(d * w for d, w in zip(digits, _NIP_WEIGHTS)) % 11
        if checksum == 10:
            continue  # invalid — retry
        digits.append(checksum)
        return "".join(str(d) for d in digits)


def generate_test_certificate(nip: str) -> tuple[bytes, bytes]:
    """Generate a self-signed certificate for KSeF TEST environment.

    Returns (cert_pem, key_pem).

    The certificate DN matches the format expected by KSeF:
      givenName=Test, surname=User, serialNumber=TINPL-{NIP}, CN=Test User, C=PL
    """
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # DN format matching C# client test utilities
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.GIVEN_NAME, "Test"),
        x509.NameAttribute(NameOID.SURNAME, "User"),
        x509.NameAttribute(NameOID.SERIAL_NUMBER, f"TINPL-{nip}"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Test User"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=730))
        .sign(private_key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def generate_test_invoice_xml(nip: str) -> bytes:
    """Generate a minimal valid FA(3) invoice XML for the given NIP.

    Returns the invoice as UTF-8 encoded bytes.
    """
    now = datetime.datetime.now(datetime.UTC)
    today = datetime.date.today()
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="http://crd.gov.pl/wzor/2025/01/09/13064/">
  <Naglowek>
    <KodFormularza kodSystemowy="FA (3)" wersjaSchemy="1-0E">FA</KodFormularza>
    <WariantFormularza>2</WariantFormularza>
    <DataWytworzeniaFa>{now.strftime("%Y-%m-%dT%H:%M:%S")}</DataWytworzeniaFa>
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
    <P_1>{today}</P_1>
    <P_2>TEST/{today.strftime("%Y")}/001</P_2>
    <P_6>{today}</P_6>
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
    return xml.encode("utf-8")
