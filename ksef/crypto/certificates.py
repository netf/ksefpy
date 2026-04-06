"""CSR generation helpers for KSeF certificate enrollment."""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509 import CertificateSigningRequestBuilder, Name, NameAttribute
from cryptography.x509.oid import NameOID

from ksef.exceptions import KSeFCryptoError


def _build_name(enrollment_info: dict[str, str]) -> Name:
    """Build an X.509 Name from *enrollment_info* dict keys.

    Accepts both snake_case keys (legacy) and the camelCase keys returned
    directly by the KSeF ``/certificates/enrollments/data`` endpoint.
    """
    attrs: list[NameAttribute] = []
    mapping = {
        # snake_case (legacy)
        "common_name": NameOID.COMMON_NAME,
        "organization": NameOID.ORGANIZATION_NAME,
        "organizational_unit": NameOID.ORGANIZATIONAL_UNIT_NAME,
        "country": NameOID.COUNTRY_NAME,
        "state": NameOID.STATE_OR_PROVINCE_NAME,
        "locality": NameOID.LOCALITY_NAME,
        "email": NameOID.EMAIL_ADDRESS,
        "serial_number": NameOID.SERIAL_NUMBER,
        "given_name": NameOID.GIVEN_NAME,
        "surname": NameOID.SURNAME,
        # camelCase (API response keys)
        "commonName": NameOID.COMMON_NAME,
        "organizationName": NameOID.ORGANIZATION_NAME,
        "organizationalUnitName": NameOID.ORGANIZATIONAL_UNIT_NAME,
        "countryName": NameOID.COUNTRY_NAME,
        "stateOrProvinceName": NameOID.STATE_OR_PROVINCE_NAME,
        "localityName": NameOID.LOCALITY_NAME,
        "serialNumber": NameOID.SERIAL_NUMBER,
        "givenName": NameOID.GIVEN_NAME,
    }
    for key, oid in mapping.items():
        value = enrollment_info.get(key)
        if value:
            attrs.append(NameAttribute(oid, value))
    if not attrs:
        raise KSeFCryptoError("enrollment_info must contain at least one DN attribute")
    return Name(attrs)


def generate_csr_rsa(
    enrollment_info: dict[str, str],
    key_size: int = 2048,
) -> tuple[str, bytes]:
    """Generate an RSA CSR for KSeF certificate enrollment.

    Returns
    -------
    (csr_b64, private_key_pem)
        *csr_b64* is the Base64-encoded DER CSR;
        *private_key_pem* is the PEM-encoded private key (PKCS#8, no encryption).
    """
    try:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        csr = (
            CertificateSigningRequestBuilder()
            .subject_name(_build_name(enrollment_info))
            .sign(private_key, hashes.SHA256())
        )
        csr_b64 = base64.b64encode(csr.public_bytes(serialization.Encoding.DER)).decode()
        key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        return csr_b64, key_pem
    except KSeFCryptoError:
        raise
    except Exception as exc:
        raise KSeFCryptoError(f"RSA CSR generation failed: {exc}") from exc


def generate_csr_ecdsa(
    enrollment_info: dict[str, str],
) -> tuple[str, bytes]:
    """Generate an ECDSA (P-256) CSR for KSeF certificate enrollment.

    Returns
    -------
    (csr_b64, private_key_pem)
        Same layout as :func:`generate_csr_rsa`.
    """
    try:
        private_key = ec.generate_private_key(ec.SECP256R1())
        csr = (
            CertificateSigningRequestBuilder()
            .subject_name(_build_name(enrollment_info))
            .sign(private_key, hashes.SHA256())
        )
        csr_b64 = base64.b64encode(csr.public_bytes(serialization.Encoding.DER)).decode()
        key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        return csr_b64, key_pem
    except KSeFCryptoError:
        raise
    except Exception as exc:
        raise KSeFCryptoError(f"ECDSA CSR generation failed: {exc}") from exc
