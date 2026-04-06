"""Create and remove test subjects and persons using the testdata API.

The KSeF TEST environment provides a /testdata namespace for setting up
integration test fixtures. This lets you create synthetic company/person
records, assign permissions, and tear everything down afterwards.

This example demonstrates:
  - Creating a test subject (a company record in the KSeF test registry).
  - Creating a test person (an individual identity on that subject).
  - Granting permissions to the test person.
  - Removing the test person and subject (clean-up).

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
    # Step 1: Generate credentials for the acting NIP (the one that will own
    # the test subject).
    owner_nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(owner_nip)
    print(f"Owner NIP: {owner_nip}")

    # Step 2: Generate a second NIP that will be our "test subject" company.
    subject_nip = generate_random_nip()
    print(f"Test subject NIP: {subject_nip}")

    # Step 3: Generate a third NIP for a test person identity.
    person_nip = generate_random_nip()
    print(f"Test person NIP: {person_nip}")

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        # Step 4: Authenticate as the owner.
        print("\nAuthenticating as owner ...")
        auth = AsyncAuthCoordinator(client)
        session = await auth.authenticate_with_certificate(
            nip=owner_nip,
            certificate=cert_pem,
            private_key=key_pem,
        )
        access_token = await session.get_access_token()
        print("  Authentication successful.")

        # Step 5: Create a test subject (company record).
        print(f"\nCreating test subject {subject_nip} ...")
        subject_resp = await client.testdata.create_subject(
            {
                "identifier": {
                    "type": "nip",
                    "value": subject_nip,
                },
                "name": f"Test Firma {subject_nip} Sp. z o.o.",
            },
            access_token=access_token,
        )
        print(f"  Response: {subject_resp}")

        # Step 6: Create a test person on that subject.
        print(f"\nCreating test person {person_nip} ...")
        person_resp = await client.testdata.create_person(
            {
                "identifier": {
                    "type": "nip",
                    "value": person_nip,
                },
                "firstName": "Jan",
                "lastName": "Kowalski",
            },
            access_token=access_token,
        )
        print(f"  Response: {person_resp}")

        # Step 7: Grant InvoiceRead permission to the test person on the subject.
        print("\nGranting permissions to test person ...")
        grant_resp = await client.testdata.grant_permissions(
            {
                "subjectIdentifier": {
                    "type": "nip",
                    "value": subject_nip,
                },
                "personIdentifier": {
                    "type": "nip",
                    "value": person_nip,
                },
                "permissions": ["InvoiceRead"],
            },
            access_token=access_token,
        )
        print(f"  Response: {grant_resp}")

        # Step 8: Clean up — remove the test person first, then the subject.
        print(f"\nRemoving test person {person_nip} ...")
        rm_person = await client.testdata.remove_person(
            {
                "identifier": {
                    "type": "nip",
                    "value": person_nip,
                },
            },
            access_token=access_token,
        )
        print(f"  Response: {rm_person}")

        print(f"\nRemoving test subject {subject_nip} ...")
        rm_subject = await client.testdata.remove_subject(
            {
                "identifier": {
                    "type": "nip",
                    "value": subject_nip,
                },
            },
            access_token=access_token,
        )
        print(f"  Response: {rm_subject}")

        print("\nClean-up complete. Done!")


if __name__ == "__main__":
    asyncio.run(main())
