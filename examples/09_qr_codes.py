"""Generate KSeF QR code verification URLs (and optionally QR images).

KSeF defines two QR code types:
  - Type 1: For online invoices (no KSeF reference number needed).
  - Type 2: For offline invoices (includes the KSeF reference number).

The URL encodes the invoice issue date, seller NIP, and a Base64URL SHA-256
hash of the structured invoice file. Scanning the QR code takes the user to
the KSeF verification portal.

This example demonstrates:
  - Building a Type 1 URL with build_qr_code_1_url().
  - Building a Type 2 URL with build_qr_code_2_url().
  - Generating a QR code image (requires ksef[qr]).

Run:
    uv run python examples/09_qr_codes.py

Requirements:
    pip install ksef            # URL generation only
    pip install ksef[qr]        # URL + image generation
"""

from __future__ import annotations

import asyncio
import base64
import datetime
import hashlib

from ksef import Environment
from ksef.crypto.qr import build_qr_code_1_url, build_qr_code_2_url
from ksef.testing import generate_random_nip, generate_test_invoice_xml


async def main() -> None:
    # Step 1: Generate a NIP and a sample invoice to hash.
    nip = generate_random_nip()
    invoice_xml = generate_test_invoice_xml(nip)
    print(f"Generated NIP: {nip}")

    # Step 2: Compute the Base64URL-encoded SHA-256 hash of the invoice bytes.
    # The hash must use URL-safe Base64 WITHOUT padding (as per KSeF spec).
    digest = hashlib.sha256(invoice_xml).digest()
    file_sha256_b64url = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    print(f"Invoice SHA-256 (Base64URL): {file_sha256_b64url}")

    invoice_date = datetime.date.today()

    # Step 3: Build a Type 1 QR URL (for online invoices, no KSeF number needed).
    url_type1 = build_qr_code_1_url(
        environment=Environment.TEST,
        invoice_date=invoice_date,
        seller_nip=nip,
        file_sha256_b64url=file_sha256_b64url,
    )
    print(f"\nQR Code Type 1 URL:\n  {url_type1}")

    # Step 4: Build a Type 2 QR URL (for offline invoices with a KSeF reference).
    # The KSeF reference number is assigned after the invoice is accepted.
    # Here we use a placeholder to illustrate the URL structure.
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
        # Save to a temporary file so you can inspect it.
        output_path = "/tmp/ksef_qr_type1.png"
        image.save(output_path)
        print(f"  QR image saved to: {output_path}")
    except ImportError:
        print("  ksef[qr] not installed — skipping image generation.")
        print("  Install with: pip install ksef[qr]")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
