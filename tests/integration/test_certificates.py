"""Integration tests for certificate endpoints."""
from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_get_certificate_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.certificates.get_limits(access_token=token)
    assert isinstance(resp, dict)
    assert "canRequest" in resp


async def test_get_enrollment_data(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.certificates.get_enrollment_data(access_token=token)
    assert isinstance(resp, dict)
    assert "commonName" in resp


async def test_certificate_enrollment_lifecycle(client: AsyncKSeFClient, auth_session: AuthSession):
    """Full certificate lifecycle: check limits -> enroll -> query -> revoke."""
    import asyncio

    token = await auth_session.get_access_token()

    # Check if we can enroll
    limits = await client.certificates.get_limits(access_token=token)
    can_request = limits.get("canRequest", False)
    if not can_request:
        pytest.skip("Certificate enrollment not available")

    # Get enrollment data for CSR
    enrollment_data = await client.certificates.get_enrollment_data(access_token=token)

    # Generate CSR — pass the camelCase enrollment_data dict directly;
    # generate_csr_rsa / _build_name now accepts the API's camelCase keys.
    from ksef.crypto.certificates import generate_csr_rsa

    csr_b64, _private_key_pem = generate_csr_rsa(enrollment_data)

    # Enroll
    enroll_resp = await client.certificates.enroll(
        {
            "certificateName": "integration-test-cert",
            "certificateType": "Authentication",
            "csr": csr_b64,
        },
        access_token=token,
    )
    assert "referenceNumber" in enroll_resp
    ref = enroll_resp["referenceNumber"]

    # Poll enrollment status
    for _ in range(10):
        status = await client.certificates.get_enrollment_status(ref, access_token=token)
        status_code = status.get("status", {}).get("code")
        if status_code == 200:
            break
        await asyncio.sleep(2)

    # Query certificates
    query_resp = await client.certificates.query({}, access_token=token)
    assert isinstance(query_resp, dict)
