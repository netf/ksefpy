"""Generate KSeF QR code verification URLs (and optionally QR images).

KSeF defines two QR code types:
  - Type 1: For online invoices (no KSeF reference number needed).
  - Type 2: For offline invoices (includes the KSeF reference number).

Run:
    uv run python examples/09_qr_codes.py

Requirements:
    pip install ksef-python            # URL generation only
    pip install ksef-python[qr]        # URL + image generation
"""

from __future__ import annotations

import base64
import datetime
import hashlib

from ksef import AsyncKSeF, Environment
from ksef.crypto.qr import build_qr_code_2_url
from ksef.testing import generate_random_nip, generate_test_certificate, generate_test_invoice_xml


def main() -> None:
    # Step 1: Generate a NIP and a sample invoice to hash.
    nip = generate_random_nip()
    invoice_xml = generate_test_invoice_xml(nip)
    print(f"Generated NIP: {nip}")

    # Step 2: Compute the Base64URL-encoded SHA-256 hash.
    digest = hashlib.sha256(invoice_xml).digest()
    file_sha256_b64url = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    print(f"Invoice SHA-256 (Base64URL): {file_sha256_b64url}")

    invoice_date = datetime.date.today()

    # Step 3: Build a Type 1 QR URL using the high-level API.
    cert_pem, key_pem = generate_test_certificate(nip)
    # qr_url() is synchronous and does not require a session
    client = AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test")
    url_type1 = client.qr_url(
        invoice_date=invoice_date,
        seller_nip=nip,
        file_hash=file_sha256_b64url,
    )
    print(f"\nQR Code Type 1 URL:\n  {url_type1}")

    # Step 4: Build a Type 2 QR URL using the low-level function directly.
    fake_ksef_number = f"{nip}-{invoice_date.strftime('%Y%m%d')}-EXAMPLE01-99"
    url_type2 = build_qr_code_2_url(
        environment=Environment.TEST,
        invoice_date=invoice_date,
        seller_nip=nip,
        file_sha256_b64url=file_sha256_b64url,
        ksef_reference_number=fake_ksef_number,
    )
    print(f"\nQR Code Type 2 URL:\n  {url_type2}")

    # Step 5: Optionally generate a QR image (requires ksef[qr]).
    print("\nAttempting to generate QR code image (requires ksef[qr]) ...")
    try:
        from ksef.crypto.qr import generate_qr_code_1

        image = generate_qr_code_1(
            environment=Environment.TEST,
            invoice_date=invoice_date,
            seller_nip=nip,
            file_sha256_b64url=file_sha256_b64url,
        )
        output_path = "/tmp/ksef_qr_type1.png"
        image.save(output_path)
        print(f"  QR image saved to: {output_path}")
    except ImportError:
        print("  ksef[qr] not installed -- skipping image generation.")
        print("  Install with: pip install ksef-python[qr]")

    print("\nDone!")


if __name__ == "__main__":
    main()
