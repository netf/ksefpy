"""Create and remove test subjects and persons on KSeF TEST.

Demonstrates the testdata endpoints for setting up integration test data:
  - create_subject / remove_subject
  - create_person / remove_person

Run:
    uv run python examples/12_test_data_setup.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Generate credentials for authentication.
    auth_nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(auth_nip)

    # Generate separate NIPs for the test entities.
    subject_nip = generate_random_nip()
    person_nip = generate_random_nip()
    # PESEL with valid date (900101) and checksum
    import random

    _PESEL_W = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    digits = [9, 0, 0, 1, 0, 1] + [random.randint(0, 9) for _ in range(4)]
    digits.append((10 - sum(d * w for d, w in zip(digits, _PESEL_W)) % 10) % 10)
    person_pesel = "".join(str(d) for d in digits)

    print(f"Auth NIP:      {auth_nip}")
    print(f"Subject NIP:   {subject_nip}")
    print(f"Person NIP:    {person_nip}")
    print(f"Person PESEL:  {person_pesel}")

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # Step 1: Authenticate.
        print("\nAuthenticating ...")
        auth = AsyncAuthCoordinator(client)
        session = await auth.authenticate_with_certificate(
            nip=auth_nip, certificate=cert_pem, private_key=key_pem,
        )
        token = await session.get_access_token()
        print("  Authentication successful.")

        # Step 2: Create a test subject.
        print(f"\nCreating test subject (NIP: {subject_nip}) ...")
        await client.testdata.create_subject(
            {"subjectNip": subject_nip, "description": "Integration test subject"},
            access_token=token,
        )
        print("  Subject created.")

        # Step 3: Create a test person.
        print(f"\nCreating test person (NIP: {person_nip}, PESEL: {person_pesel}) ...")
        await client.testdata.create_person(
            {
                "nip": person_nip,
                "pesel": person_pesel,
                "isBailiff": False,
                "description": "Integration test person entity",
            },
            access_token=token,
        )
        print("  Person created.")

        # Step 4: Clean up — remove person first, then subject.
        print(f"\nRemoving test person (NIP: {person_nip}) ...")
        await client.testdata.remove_person(
            {"nip": person_nip},
            access_token=token,
        )
        print("  Person removed.")

        print(f"\nRemoving test subject (NIP: {subject_nip}) ...")
        await client.testdata.remove_subject(
            {"subjectNip": subject_nip},
            access_token=token,
        )
        print("  Subject removed.")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
