import httpx
import pytest
import respx

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.coordinators.online_session import AsyncOnlineSessionManager
from ksef.crypto.service import CryptographyService
from ksef.environments import Environment
from ksef.models.auth import TokenInfo

BASE = "https://api-test.ksef.mf.gov.pl/v2"


def _make_session(client):
    return AuthSession(
        client=client,
        access_token=TokenInfo(token="access-jwt", valid_until="2099-01-01T00:00:00+00:00"),
        refresh_token=TokenInfo(token="refresh-jwt", valid_until="2099-01-07T00:00:00+00:00"),
    )


@respx.mock
@pytest.mark.asyncio
async def test_online_session_send_invoice():
    respx.post(f"{BASE}/sessions/online").mock(
        return_value=httpx.Response(201, json={
            "referenceNumber": "sess-1",
            "validUntil": "2026-04-07T10:00:00+00:00",
        })
    )
    respx.post(f"{BASE}/sessions/online/sess-1/invoices").mock(
        return_value=httpx.Response(201, json={"referenceNumber": "inv-1"})
    )
    respx.post(f"{BASE}/sessions/online/sess-1/close").mock(
        return_value=httpx.Response(200, json={})
    )

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        session = _make_session(client)

        import datetime

        from cryptography import x509
        from cryptography.hazmat.primitives import hashes
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

        crypto = CryptographyService()
        crypto.set_symmetric_key_certificate(cert)

        manager = AsyncOnlineSessionManager(client, session, crypto=crypto)

        async with manager.open(schema_version="FA(3)") as online:
            result = await online.send_invoice_xml(b"<Faktura>test</Faktura>")
            assert result.reference_number == "inv-1"
