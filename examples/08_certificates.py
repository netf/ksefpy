"""Inspect certificate limits, retrieve enrollment data, and generate a CSR.

KSeF supports enrolling X.509 certificates that can be used for
authentication instead of API tokens.

Run:
    uv run python examples/08_certificates.py

Requirements:
    pip install ksefpy[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.crypto.certificates import generate_csr_ecdsa, generate_csr_rsa
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 2: Check certificate limits.
        print("\nFetching certificate limits ...")
        limits = await client.get_certificate_limits()
        max_certs = limits.get("maxCertificates") or limits.get("max_certificates", "?")
        used_certs = limits.get("usedCertificates") or limits.get("used_certificates", "?")
        print(f"  Max certificates allowed: {max_certs}")
        print(f"  Currently enrolled:       {used_certs}")

        # Step 3: Fetch enrollment data (DN attributes for CSR).
        print("\nFetching certificate enrollment data ...")
        enrollment_data = await client.get_enrollment_data()
        print(f"  Enrollment data: {enrollment_data}")

        # Step 4: Generate an RSA CSR from the enrollment data.
        print("\nGenerating RSA-2048 CSR ...")
        dn_info = dict(enrollment_data)
        if not dn_info.get("commonName") and not dn_info.get("common_name"):
            dn_info["commonName"] = f"Test User {nip}"
        if not dn_info.get("serialNumber") and not dn_info.get("serial_number"):
            dn_info["serialNumber"] = f"TINPL-{nip}"
        if not dn_info.get("countryName") and not dn_info.get("country"):
            dn_info["countryName"] = "PL"

        csr_b64, rsa_key_pem = generate_csr_rsa(dn_info, key_size=2048)
        print(f"  RSA CSR (first 60 chars): {csr_b64[:60]}...")

        # Step 5: Generate an ECDSA (P-256) CSR as an alternative.
        print("\nGenerating ECDSA P-256 CSR ...")
        ecdsa_csr_b64, ecdsa_key_pem = generate_csr_ecdsa(dn_info)
        print(f"  ECDSA CSR (first 60 chars): {ecdsa_csr_b64[:60]}...")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
