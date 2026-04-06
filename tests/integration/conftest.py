"""Shared fixtures for integration tests against KSeF TEST environment."""

from __future__ import annotations

import os

import pytest
import pytest_asyncio

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator
from ksef.testing import generate_random_nip, generate_test_certificate

# All async tests and fixtures in this directory use a single session-scoped event loop
pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(scope="session")
def nip() -> str:
    return os.environ.get("KSEF_TEST_NIP") or generate_random_nip()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client():
    async with AsyncKSeFClient(environment=Environment.TEST) as c:
        yield c


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def auth_session(client, nip):
    coordinator = AsyncAuthCoordinator(client)
    token = os.environ.get("KSEF_TEST_TOKEN")
    if token:
        return await coordinator.authenticate_with_token(nip=nip, ksef_token=token)
    cert_pem, key_pem = generate_test_certificate(nip)
    return await coordinator.authenticate_with_certificate(
        nip=nip, certificate=cert_pem, private_key=key_pem,
    )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def access_token(auth_session):
    return await auth_session.get_access_token()
