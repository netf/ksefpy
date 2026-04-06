"""Use the synchronous KSeFClient — no async/await required.

Every operation available on AsyncKSeFClient has an equivalent synchronous
version via KSeFClient. Under the hood, KSeFClient runs the async event
loop on a dedicated daemon thread, so it is safe to use from regular
synchronous code including scripts, Django views, or Celery tasks.

This example mirrors 02_authenticate_certificate.py but uses the sync API.

Run:
    uv run python examples/10_sync_client.py

Requirements:
    pip install ksef[xades]
"""

from __future__ import annotations

from ksef import Environment, KSeFClient
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.testing import generate_random_nip, generate_test_certificate


def _authenticate(client: KSeFClient, nip: str, cert_pem: bytes, key_pem: bytes):
    """Authenticate synchronously by wrapping AsyncAuthCoordinator.

    The KSeFClient's underlying SyncWrapper exposes the async client via
    _wrapper._async_client.  We drive the auth coordinator via the async
    client so the coordinator can call async sub-methods internally, but
    the wrapper's _run_coroutine bridges the thread boundary for us.
    """
    async_client = client._async_client
    auth = AsyncAuthCoordinator(async_client)
    # Use the SyncWrapper's run helper to execute the coroutine synchronously.
    return client._wrapper._run_coroutine(
        auth.authenticate_with_certificate(
            nip=nip,
            certificate=cert_pem,
            private_key=key_pem,
        )
    )


def main() -> None:
    # Step 1: Generate a random NIP and matching self-signed certificate.
    nip = generate_random_nip()
    cert_pem, key_pem = generate_test_certificate(nip)
    print(f"Generated NIP:       {nip}")

    # Step 2: Open the synchronous client with a context manager.
    # KSeFClient implements __enter__/__exit__ so you can use 'with'.
    with KSeFClient(environment=Environment.TEST) as client:
        # Step 3: Authenticate.  We drive AsyncAuthCoordinator through the
        # sync wrapper so we get a proper AuthSession back.
        print("\nAuthenticating (sync) ...")
        session = _authenticate(client, nip, cert_pem, key_pem)
        print("  Authentication successful.")

        # Step 4: Retrieve the access token synchronously.
        access_token = client._wrapper._run_coroutine(session.get_access_token())
        print(f"  Access token (first 40 chars): {access_token[:40]}...")
        print(f"  Expires at:                    {session.access_token_info.valid_until}")

        # Step 5: Call a low-level endpoint synchronously.
        # client.auth exposes all AuthClient methods as sync callables.
        print("\nFetching a fresh challenge (sync low-level call) ...")
        challenge = client.auth.get_challenge()
        print(f"  Challenge:   {challenge.challenge}")
        print(f"  Timestamp:   {challenge.timestamp_ms}")

    print("\nClient closed.  Done!")


if __name__ == "__main__":
    main()
