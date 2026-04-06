from datetime import date

from ksef.crypto.qr import build_qr_code_1_url
from ksef.environments import Environment


def test_qr_code_1_url_structure():
    url = build_qr_code_1_url(
        environment=Environment.PRODUCTION,
        invoice_date=date(2026, 4, 6),
        seller_nip="1234567890",
        file_sha256_b64url="abc123def456",
    )
    assert url.startswith("https://qr.ksef.mf.gov.pl/")
    assert "06-04-2026" in url
    assert "1234567890" in url
    assert "abc123def456" in url


def test_qr_code_1_url_test_environment():
    url = build_qr_code_1_url(
        environment=Environment.TEST,
        invoice_date=date(2026, 1, 15),
        seller_nip="9876543210",
        file_sha256_b64url="hashvalue",
    )
    assert url.startswith("https://qr-test.ksef.mf.gov.pl/")
