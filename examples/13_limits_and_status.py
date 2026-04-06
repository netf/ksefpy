"""Query context limits, subject limits, rate limits, and session status.

KSeF enforces several kinds of limits:
  - Context limits  -- per-session limits (max invoices, max open sessions).
  - Subject limits  -- per-NIP limits (max enrolled certificates).
  - Rate limits     -- API throttling (requests per second/minute).

The get_limits() method fetches all three in parallel.

Run:
    uv run python examples/13_limits_and_status.py

Requirements:
    pip install ksefpy[xades]
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
        # Step 2: Fetch all limits in one call.
        print("\nFetching all limits ...")
        limits = await client.get_limits()
        print(f"  Context limits: {limits.context}")
        print(f"  Subject limits: {limits.subject}")
        print(f"  Rate limits:    {limits.rate}")

        # Step 3: List active auth sessions (low-level).
        print("\nListing active authentication sessions ...")
        await client._ensure_auth()
        access_token = await client._get_access_token()
        sessions_resp = await client._client.sessions.list_sessions(
            access_token=access_token,
            params={"pageSize": 10, "pageNumber": 0},
        )
        active = sessions_resp.get("sessions") or sessions_resp.get("items") or []
        total = sessions_resp.get("count") or sessions_resp.get("total", len(active))
        print(f"  Active sessions: {total}")
        for s in active[:5]:
            ref = s.get("referenceNumber") or s.get("reference_number", "?")
            created = s.get("createdAt") or s.get("created_at", "?")
            print(f"    - {ref} (created: {created})")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
