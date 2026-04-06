import base64
import os

import pytest

from ksef.crypto.service import CryptographyService


def test_encrypt_decrypt_aes256_roundtrip():
    crypto = CryptographyService()
    key = os.urandom(32)
    iv = os.urandom(16)
    plaintext = b"Hello KSeF invoice content!"

    encrypted = crypto.encrypt_aes256(plaintext, key, iv)
    assert encrypted != plaintext

    decrypted = crypto.decrypt_aes256(encrypted, key, iv)
    assert decrypted == plaintext


def test_encrypt_aes256_uses_pkcs7_padding():
    crypto = CryptographyService()
    key = os.urandom(32)
    iv = os.urandom(16)
    plaintext = b"fifteen chars!!"
    assert len(plaintext) == 15

    encrypted = crypto.encrypt_aes256(plaintext, key, iv)
    assert len(encrypted) == 16

    decrypted = crypto.decrypt_aes256(encrypted, key, iv)
    assert decrypted == plaintext


def test_get_metadata():
    crypto = CryptographyService()
    content = b"test invoice xml content"
    metadata = crypto.get_metadata(content)
    assert metadata.file_size == len(content)
    assert len(metadata.hash_sha) == 64  # SHA-256 hex


def test_generate_session_materials():
    crypto = CryptographyService()
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import hashes
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    import datetime

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
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

    crypto.set_symmetric_key_certificate(cert)
    materials = crypto.generate_session_materials()

    assert len(materials.key) == 32
    assert len(materials.iv) == 16
    assert len(materials.encrypted_key) > 0

    from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
    decrypted_key = private_key.decrypt(
        materials.encrypted_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    assert decrypted_key == materials.key


def test_encrypt_ksef_token():
    crypto = CryptographyService()
    from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
    from cryptography.hazmat.primitives import hashes
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    import datetime

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
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

    crypto.set_ksef_token_certificate(cert)
    encrypted = crypto.encrypt_ksef_token(token="my-token", timestamp_ms=1775386800000)

    decrypted = private_key.decrypt(
        base64.b64decode(encrypted),
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    assert decrypted == b"my-token|1775386800000"
