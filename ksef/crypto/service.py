"""Core cryptography service for KSeF API interactions."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ksef.exceptions import KSeFCryptoError

if TYPE_CHECKING:
    from cryptography import x509


@dataclass
class FileMetadata:
    """Metadata for a file processed by KSeF."""

    hash_sha: str
    file_size: int


@dataclass
class SessionMaterials:
    """Session encryption materials."""

    key: bytes
    iv: bytes
    encrypted_key: bytes


class CryptographyService:
    """Provides cryptographic operations for KSeF API interactions."""

    def __init__(self) -> None:
        self._symmetric_key_cert: x509.Certificate | None = None
        self._ksef_token_cert: x509.Certificate | None = None

    # ------------------------------------------------------------------
    # Symmetric (AES-256-CBC)
    # ------------------------------------------------------------------

    def encrypt_aes256(self, plaintext: bytes, key: bytes, iv: bytes) -> bytes:
        """Encrypt *plaintext* with AES-256-CBC + PKCS#7 padding."""
        try:
            padder = padding.PKCS7(128).padder()
            padded = padder.update(plaintext) + padder.finalize()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            return encryptor.update(padded) + encryptor.finalize()
        except Exception as exc:
            raise KSeFCryptoError(f"AES-256 encryption failed: {exc}") from exc

    def decrypt_aes256(self, ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
        """Decrypt *ciphertext* with AES-256-CBC + PKCS#7 unpadding."""
        try:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            return unpadder.update(padded) + unpadder.finalize()
        except Exception as exc:
            raise KSeFCryptoError(f"AES-256 decryption failed: {exc}") from exc

    # ------------------------------------------------------------------
    # File metadata
    # ------------------------------------------------------------------

    def get_metadata(self, content: bytes) -> FileMetadata:
        """Return Base64-encoded SHA-256 digest and byte length of *content*.

        The KSeF API expects hashes in Base64 (not hex).
        """
        return FileMetadata(
            hash_sha=base64.b64encode(hashlib.sha256(content).digest()).decode(),
            file_size=len(content),
        )

    # ------------------------------------------------------------------
    # RSA-OAEP helpers
    # ------------------------------------------------------------------

    def _rsa_encrypt(self, cert: x509.Certificate, plaintext: bytes) -> bytes:
        """Encrypt *plaintext* with the public key from *cert* using RSA-OAEP/SHA-256."""
        public_key = cert.public_key()
        return public_key.encrypt(  # type: ignore[union-attr]
            plaintext,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    # ------------------------------------------------------------------
    # Session materials
    # ------------------------------------------------------------------

    def generate_session_materials(self) -> SessionMaterials:
        """Generate a fresh AES-256 key + IV and encrypt the key with the stored certificate."""
        if self._symmetric_key_cert is None:
            raise KSeFCryptoError("No symmetric key certificate set. Call set_symmetric_key_certificate() first.")
        try:
            key = os.urandom(32)
            iv = os.urandom(16)
            encrypted_key = self._rsa_encrypt(self._symmetric_key_cert, key)
            return SessionMaterials(key=key, iv=iv, encrypted_key=encrypted_key)
        except KSeFCryptoError:
            raise
        except Exception as exc:
            raise KSeFCryptoError(f"Failed to generate session materials: {exc}") from exc

    # ------------------------------------------------------------------
    # Token encryption
    # ------------------------------------------------------------------

    def encrypt_ksef_token(self, token: str, timestamp_ms: int) -> str:
        """Encrypt ``{token}|{timestamp_ms}`` with RSA-OAEP and return Base64."""
        if self._ksef_token_cert is None:
            raise KSeFCryptoError("No KSeF token certificate set. Call set_ksef_token_certificate() first.")
        try:
            plaintext = f"{token}|{timestamp_ms}".encode()
            encrypted = self._rsa_encrypt(self._ksef_token_cert, plaintext)
            return base64.b64encode(encrypted).decode()
        except KSeFCryptoError:
            raise
        except Exception as exc:
            raise KSeFCryptoError(f"Failed to encrypt KSeF token: {exc}") from exc

    # ------------------------------------------------------------------
    # Certificate setters
    # ------------------------------------------------------------------

    def set_symmetric_key_certificate(self, cert: x509.Certificate) -> None:
        """Set the certificate used to encrypt AES session keys."""
        self._symmetric_key_cert = cert

    def set_ksef_token_certificate(self, cert: x509.Certificate) -> None:
        """Set the certificate used to encrypt KSeF auth tokens."""
        self._ksef_token_cert = cert
