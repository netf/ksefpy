"""Shared fixtures for integration tests against KSeF TEST environment."""

from __future__ import annotations

import os

import pytest
import pytest_asyncio

from ksef import AsyncKSeF
from ksef.testing import generate_random_nip

# All async tests and fixtures in this directory use a single session-scoped event loop
pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(scope="session")
def nip() -> str:
    return os.environ.get("KSEF_TEST_NIP") or generate_random_nip()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client(nip):
    token = os.environ.get("KSEF_TEST_TOKEN")
    if token:
        c = AsyncKSeF(nip=nip, token=token, env="test")
    else:
        from ksef.testing import generate_test_certificate

        cert_pem, key_pem = generate_test_certificate(nip)
        c = AsyncKSeF(nip=nip, cert=cert_pem, key=key_pem, env="test")
    async with c:
        yield c
