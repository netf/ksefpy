"""Query personal permissions and check attachment status.

The permissions sub-system controls which roles and operations a given
identity (person or entity) is authorised to perform on a NIP context.

This example demonstrates:
  - Querying personal grants (what the authenticated user can do).
  - Getting entity role definitions.
  - Checking the attachment (Pełnomocnictwo) status for the current context.

Run:
    uv run python examples/07_permissions.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
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

        # Step 3: Query personal grants — what can the authenticated user do?
        print("\nQuerying personal grants ...")
        personal_resp = await client.permissions.query_personal(
            {
                "pageSize": 10,
                "pageNumber": 0,
            },
            access_token=access_token,
        )
        grants = personal_resp.get("grants") or personal_resp.get("items") or []
        total = personal_resp.get("count") or personal_resp.get("total", len(grants))
        print(f"  Total personal grants: {total}")
        for g in grants[:5]:  # show at most 5
            role = g.get("roleName") or g.get("role_name") or g.get("roleType", "?")
            print(f"    - {role}")

        # Step 4: Get entity role definitions — reference data for the roles system.
        print("\nQuerying entity roles ...")
        roles_resp = await client.permissions.query_entity_roles(access_token=access_token)
        roles = roles_resp.get("roles") or roles_resp.get("items") or []
        print(f"  Available entity roles: {len(roles)}")
        for r in roles[:5]:  # show at most 5
            name = r.get("roleName") or r.get("name", "?")
            print(f"    - {name}")

        # Step 5: Check attachment (Pełnomocnictwo) status.
        # An "attachment" in KSeF context means a formal power of attorney
        # submitted to KSeF that allows acting on behalf of another entity.
        print("\nChecking attachment status ...")
        attachment = await client.permissions.get_attachment_status(access_token=access_token)
        status = attachment.get("status") or attachment.get("attachmentStatus", "unknown")
        print(f"  Attachment status: {status}")
        print(f"  Full response:     {attachment}")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
