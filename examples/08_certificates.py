"""Inspect certificate limits, retrieve enrollment data, and generate a CSR.

KSeF supports enrolling X.509 certificates that can be used for
authentication instead of API tokens. Before enrolling, you can check
how many certificates you are allowed and retrieve the DN attributes
that the CSR must contain.

This example demonstrates:
  - Fetching certificate limits (how many certs you can enroll).
  - Fetching certificate enrollment data (the required DN attributes).
  - Generating an RSA CSR from that enrollment data (local only — not submitted).
  - Generating an ECDSA CSR as an alternative.

Run:
    uv run python examples/08_certificates.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.crypto.certificates import generate_csr_ecdsa, generate_csr_rsa
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # Step 2: Authenticate.
        print("\nAuthenticating ...")
        auth = AsyncAuthCoordinator(client)
        session = await auth.authenticate_with_certificate(
            nip=nip,
            certificate=cert_pem,
            private_key=key_pem,
        )
        access_token = await session.get_access_token()
        print("  Authentication successful.")

        # Step 3: Check certificate limits for this NIP context.
        print("\nFetching certificate limits ...")
        limits = await client.certificates.get_limits(access_token=access_token)
        print(f"  Limits response: {limits}")
        max_certs = limits.get("maxCertificates") or limits.get("max_certificates", "?")
        used_certs = limits.get("usedCertificates") or limits.get("used_certificates", "?")
        print(f"  Max certificates allowed: {max_certs}")
        print(f"  Currently enrolled:       {used_certs}")

        # Step 4: Fetch the enrollment data — this gives us the DN attributes
        # that our CSR subject name must include.
        print("\nFetching certificate enrollment data ...")
        enrollment_data = await client.certificates.get_enrollment_data(access_token=access_token)
        print(f"  Enrollment data: {enrollment_data}")

        # Step 5: Generate an RSA CSR from the enrollment data.
        # generate_csr_rsa() accepts both snake_case and camelCase DN keys
        # (as returned by the enrollment data endpoint).
        print("\nGenerating RSA-2048 CSR ...")
        # Merge enrollment data with a fallback common name in case the API
        # returned an empty object (possible on TEST for new NIPs).
        dn_info = dict(enrollment_data)
        if not dn_info.get("commonName") and not dn_info.get("common_name"):
            dn_info["commonName"] = f"Test User {nip}"
        if not dn_info.get("serialNumber") and not dn_info.get("serial_number"):
            dn_info["serialNumber"] = f"TINPL-{nip}"
        if not dn_info.get("countryName") and not dn_info.get("country"):
            dn_info["countryName"] = "PL"

        csr_b64, rsa_key_pem = generate_csr_rsa(dn_info, key_size=2048)
        print(f"  RSA CSR (Base64, first 60 chars): {csr_b64[:60]}...")
        print(f"  Private key PEM size: {len(rsa_key_pem)} bytes")

        # Step 6: Generate an ECDSA (P-256) CSR — smaller and faster than RSA.
        print("\nGenerating ECDSA P-256 CSR ...")
        ecdsa_csr_b64, ecdsa_key_pem = generate_csr_ecdsa(dn_info)
        print(f"  ECDSA CSR (Base64, first 60 chars): {ecdsa_csr_b64[:60]}...")
        print(f"  Private key PEM size: {len(ecdsa_key_pem)} bytes")

        print("\nNote: To submit the CSR for enrollment, call:")
        print("  await client.certificates.enroll({'csr': csr_b64, ...}, access_token=token)")
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
