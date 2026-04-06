"""Query personal permissions and check attachment status.

The permissions sub-system controls which roles and operations a given
identity is authorised to perform on a NIP context.

Run:
    uv run python examples/07_permissions.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

import asyncio

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip, generate_test_certificate


async def main() -> None:
    # Step 1: Generate credentials.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP: {nip}")

    async with AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test") as client:
        # Step 2: Query personal grants.
        print("\nQuerying personal permissions ...")
        resp = await client.query_permissions(pageSize=10, pageNumber=0)
        grants = resp.get("grants") or resp.get("items") or []
        total = resp.get("count") or resp.get("total", len(grants))
        print(f"  Total personal grants: {total}")
        for g in grants[:5]:
            role = g.get("roleName") or g.get("role_name") or g.get("roleType", "?")
            print(f"    - {role}")

        # Step 3: Check attachment (power of attorney) status.
        print("\nChecking attachment status ...")
        attachment = await client.get_attachment_status()
        status = attachment.get("status") or attachment.get("attachmentStatus", "unknown")
        print(f"  Attachment status: {status}")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
