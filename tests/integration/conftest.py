"""Shared fixtures for integration tests against KSeF TEST environment."""

from __future__ import annotations

import asyncio
import os

import pytest

from ksef import AsyncKSeFClient, Environment
from ksef.coordinators.auth import AsyncAuthCoordinator, AuthSession
from ksef.testing import generate_random_nip, generate_test_certificate


@pytest.fixture(scope="session")
def nip() -> str:
    return os.environ.get("KSEF_TEST_NIP") or generate_random_nip()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client():
    async with AsyncKSeFClient(environment=Environment.TEST) as c:
        yield c


@pytest.fixture(scope="session")
async def auth_session(client, nip):
    coordinator = AsyncAuthCoordinator(client)
    token = os.environ.get("KSEF_TEST_TOKEN")
    if token:
        return await coordinator.authenticate_with_token(nip=nip, ksef_token=token)
    cert_pem, key_pem = generate_test_certificate(nip)
    return await coordinator.authenticate_with_certificate(
        nip=nip, certificate=cert_pem, private_key=key_pem,
    )


@pytest.fixture(scope="session")
async def access_token(auth_session):
    return await auth_session.get_access_token()
