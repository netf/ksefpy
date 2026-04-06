import httpx
import pytest
import respx

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AsyncAuthCoordinator, AuthSession
from ksef.environments import Environment

BASE = "https://api-test.ksef.mf.gov.pl/v2"


def _mock_challenge():
    return respx.post(f"{BASE}/auth/challenge").mock(
        return_value=httpx.Response(200, json={
            "challenge": "test-challenge",
            "timestamp": "2026-04-06T10:00:00+00:00",
            "timestampMs": 1775386800000,
            "clientIp": "1.2.3.4",
        })
    )


def _mock_ksef_token_auth():
    return respx.post(f"{BASE}/auth/ksef-token").mock(
        return_value=httpx.Response(200, json={
            "referenceNumber": "auth-ref-1",
            "authenticationToken": {"token": "temp-tok", "validUntil": "2026-04-06T10:10:00+00:00"},
        })
    )


def _mock_auth_status_complete():
    return respx.get(f"{BASE}/auth/auth-ref-1").mock(
        return_value=httpx.Response(200, json={
            "startDate": "2026-04-06T10:00:00+00:00",
            "status": {"code": "200", "description": "OK"},
            "isTokenRedeemed": False,
        })
    )


def _mock_redeem():
    return respx.post(f"{BASE}/auth/token/redeem").mock(
        return_value=httpx.Response(200, json={
            "accessToken": {"token": "access-jwt-123", "validUntil": "2026-04-06T10:15:00+00:00"},
            "refreshToken": {"token": "refresh-jwt-456", "validUntil": "2026-04-13T10:00:00+00:00"},
        })
    )


def _mock_public_keys():
    import base64
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    cert_b64 = base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode()

    return respx.get(f"{BASE}/security/public-key-certificates").mock(
        return_value=httpx.Response(200, json=[
            {
                "certificate": cert_b64,
                "validFrom": "2026-01-01T00:00:00Z",
                "validTo": "2027-01-01T00:00:00Z",
                "usage": ["KSEF_TOKEN_ENCRYPTION", "SYMMETRIC_KEY_ENCRYPTION"],
            },
        ])
    )


@respx.mock
@pytest.mark.asyncio
async def test_authenticate_with_token():
    _mock_public_keys()
    _mock_challenge()
    _mock_ksef_token_auth()
    _mock_auth_status_complete()
    _mock_redeem()

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        coordinator = AsyncAuthCoordinator(client)
        session = await coordinator.authenticate_with_token(
            nip="1234567890",
            ksef_token="my-test-token",
        )
        assert isinstance(session, AuthSession)
        token = await session.get_access_token()
        assert token == "access-jwt-123"
