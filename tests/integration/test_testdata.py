"""Integration tests for test data management endpoints."""
from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.testing import generate_random_nip

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_create_and_remove_subject(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    test_nip = generate_random_nip()
    await client.testdata.create_subject(
        {"subjectNip": test_nip, "description": "Integration Test Subject"},
        access_token=token,
    )
    # API returns 200 with empty body on success
    await client.testdata.remove_subject({"subjectNip": test_nip}, access_token=token)


async def test_create_and_remove_person(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    test_nip = generate_random_nip()
    # Generate PESEL with valid date part (YYMMDD) + random suffix + checksum
    import random

    _PESEL_WEIGHTS = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    date_part = [9, 0, 0, 1, 0, 1]  # 900101 = Jan 1, 1990
    rest = [random.randint(0, 9) for _ in range(4)]
    digits = date_part + rest
    checksum = (10 - sum(d * w for d, w in zip(digits, _PESEL_WEIGHTS)) % 10) % 10
    digits.append(checksum)
    test_pesel = "".join(str(d) for d in digits)
    await client.testdata.create_person(
        {"nip": test_nip, "pesel": test_pesel, "isBailiff": False, "description": "Integration test person entity"},
        access_token=token,
    )
    await client.testdata.remove_person({"nip": test_nip}, access_token=token)
