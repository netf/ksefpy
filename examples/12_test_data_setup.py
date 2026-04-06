"""Create and remove test subjects and persons on KSeF TEST.

Demonstrates the testdata endpoints for setting up integration test data.
These are low-level endpoints not exposed in the simplified API, so we
access the internal client directly.

Run:
    uv run python examples/12_test_data_setup.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio
import random

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Generate credentials for authentication.
    auth_nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(auth_nip)

    # Generate separate NIPs for the test entities.
    subject_nip = generate_random_nip()
    person_nip = generate_random_nip()

    # PESEL with valid date (900101) and checksum
    _PESEL_W = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    digits = [9, 0, 0, 1, 0, 1] + [random.randint(0, 9) for _ in range(4)]
    digits.append((10 - sum(d * w for d, w in zip(digits, _PESEL_W)) % 10) % 10)
    person_pesel = "".join(str(d) for d in digits)

    print(f"Auth NIP:      {auth_nip}")
    print(f"Subject NIP:   {subject_nip}")
    print(f"Person NIP:    {person_nip}")
    print(f"Person PESEL:  {person_pesel}")

    async with AsyncKSeF(nip=auth_nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Ensure auth is initialized for low-level access
        await client._ensure_auth()
        access_token = await client._get_access_token()

        # Step 1: Create a test subject.
        print(f"\nCreating test subject (NIP: {subject_nip}) ...")
        await client._client.testdata.create_subject(
            {"subjectNip": subject_nip, "description": "Integration test subject"},
            access_token=access_token,
        )
        print("  Subject created.")

        # Step 2: Create a test person.
        print(f"\nCreating test person (NIP: {person_nip}, PESEL: {person_pesel}) ...")
        await client._client.testdata.create_person(
            {
                "nip": person_nip,
                "pesel": person_pesel,
                "isBailiff": False,
                "description": "Integration test person entity",
            },
            access_token=access_token,
        )
        print("  Person created.")

        # Step 3: Clean up.
        print(f"\nRemoving test person (NIP: {person_nip}) ...")
        await client._client.testdata.remove_person(
            {"nip": person_nip},
            access_token=access_token,
        )
        print("  Person removed.")

        print(f"\nRemoving test subject (NIP: {subject_nip}) ...")
        await client._client.testdata.remove_subject(
            {"subjectNip": subject_nip},
            access_token=access_token,
        )
        print("  Subject removed.")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
