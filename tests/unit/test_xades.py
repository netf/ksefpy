import datetime
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


@pytest.fixture
def test_cert_and_key():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Test KSeF"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def test_xades_sign_produces_signed_xml(test_cert_and_key):
    pytest.importorskip("signxml")
    from ksef.crypto.xades import XAdESService

    cert_pem, key_pem = test_cert_and_key
    xml_doc = "<AuthTokenRequest><Challenge>abc123</Challenge></AuthTokenRequest>"

    xades = XAdESService()
    signed = xades.sign(xml_doc, certificate=cert_pem, private_key=key_pem)

    assert isinstance(signed, str)
    assert "<ds:Signature" in signed or "<Signature" in signed
    assert "abc123" in signed


def test_xades_sign_raises_on_invalid_key():
    pytest.importorskip("signxml")
    from ksef.crypto.xades import XAdESService

    xades = XAdESService()
    with pytest.raises(Exception):
        xades.sign("<doc/>", certificate=b"bad", private_key=b"bad")
