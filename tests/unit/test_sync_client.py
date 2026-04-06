import httpx
import respx

from ksef import Environment, KSeFClient

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@respx.mock
def test_sync_client_get_challenge():
    respx.post(f"{BASE}/auth/challenge").mock(
        return_value=httpx.Response(200, json={
            "challenge": "sync-challenge",
            "timestamp": "2026-04-06T10:00:00+00:00",
            "timestampMs": 1775386800000,
        })
    )
    with KSeFClient(environment=Environment.TEST) as client:
        result = client.auth.get_challenge()
        assert result.challenge == "sync-challenge"


def test_sync_client_has_all_sub_clients():
    with KSeFClient(environment=Environment.TEST) as client:
        assert hasattr(client, "auth")
        assert hasattr(client, "online")
        assert hasattr(client, "batch")
        assert hasattr(client, "invoices")
        assert hasattr(client, "permissions")
        assert hasattr(client, "certificates")
        assert hasattr(client, "tokens")
        assert hasattr(client, "limits")
