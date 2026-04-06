"""Query context limits, subject limits, rate limits, and active auth sessions.

KSeF enforces several kinds of limits:

  - Context limits  — per-authenticated-session limits (e.g. max invoices
                      per online session, max open sessions at once).
  - Subject limits  — per-NIP limits (e.g. max enrolled certificates).
  - Rate limits     — API-level throttling limits (requests per second/minute).

Additionally, you can list all active authentication sessions for your NIP
and invalidate them individually or all at once.

Run:
    uv run python examples/13_limits_and_status.py

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

        # Step 3: Fetch context limits — these reflect the current session's
        # allowed operations (e.g. max invoices per online session).
        print("\nFetching context limits ...")
        ctx_limits = await client.limits.get_context_limits(access_token=access_token)
        print(f"  Context limits: {ctx_limits}")

        # Step 4: Fetch subject limits — NIP-level caps.
        print("\nFetching subject limits ...")
        sub_limits = await client.limits.get_subject_limits(access_token=access_token)
        print(f"  Subject limits: {sub_limits}")

        # Step 5: Fetch API rate limits — how many requests per time window
        # you are allowed to make and how many remain.
        print("\nFetching rate limits ...")
        rate_limits = await client.limits.get_rate_limits(access_token=access_token)
        print(f"  Rate limits: {rate_limits}")

        # Step 6: List active authentication sessions for this NIP.
        # Each entry represents an open auth session (access + refresh token pair).
        print("\nListing active authentication sessions ...")
        sessions_resp = await client.sessions.list_sessions(
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
