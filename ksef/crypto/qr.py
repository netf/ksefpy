"""QR code URL generation and image creation for KSeF invoices."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from ksef.exceptions import KSeFCryptoError

if TYPE_CHECKING:
    from ksef.environments import Environment


def build_qr_code_1_url(
    environment: Environment,
    invoice_date: date,
    seller_nip: str,
    file_sha256_b64url: str,
) -> str:
    """Build the KSeF QR Code Type 1 verification URL.

    The URL encodes the invoice date (dd-MM-yyyy), seller NIP, and a
    Base64URL-encoded SHA-256 hash of the invoice file.

    Parameters
    ----------
    environment:
        Target KSeF environment (TEST, DEMO, or PRODUCTION).
    invoice_date:
        Issue date of the invoice.
    seller_nip:
        Seller's NIP (tax identifier).
    file_sha256_b64url:
        Base64URL-encoded SHA-256 hash of the structured invoice file.

    Returns
    -------
    str
        Full verification URL.
    """
    date_str = invoice_date.strftime("%d-%m-%Y")
    base = environment.qr_base_url.rstrip("/")
    return f"{base}/{date_str}/{seller_nip}/{file_sha256_b64url}"


def build_qr_code_2_url(
    environment: Environment,
    invoice_date: date,
    seller_nip: str,
    file_sha256_b64url: str,
    ksef_reference_number: str,
) -> str:
    """Build the KSeF QR Code Type 2 URL (offline invoices with KSeF reference).

    Parameters
    ----------
    environment:
        Target KSeF environment.
    invoice_date:
        Issue date of the invoice.
    seller_nip:
        Seller's NIP (tax identifier).
    file_sha256_b64url:
        Base64URL-encoded SHA-256 hash of the structured invoice file.
    ksef_reference_number:
        The KSeF reference number assigned to the invoice.

    Returns
    -------
    str
        Full verification URL including the KSeF reference number.
    """
    date_str = invoice_date.strftime("%d-%m-%Y")
    base = environment.qr_base_url.rstrip("/")
    return f"{base}/{date_str}/{seller_nip}/{file_sha256_b64url}/{ksef_reference_number}"


def generate_qr_code_1(
    environment: Environment,
    invoice_date: date,
    seller_nip: str,
    file_sha256_b64url: str,
    *,
    box_size: int = 10,
    border: int = 4,
) -> Any:
    """Generate a QR code image for a KSeF Type 1 verification URL.

    Requires the ``[qr]`` optional extra::

        pip install ksef[qr]

    Parameters
    ----------
    environment, invoice_date, seller_nip, file_sha256_b64url:
        Passed directly to :func:`build_qr_code_1_url`.
    box_size:
        Pixel size of each QR module box.
    border:
        Number of box-widths of white border around the QR code.

    Returns
    -------
    PIL.Image.Image
        QR code image object.

    Raises
    ------
    KSeFCryptoError
        If ``qrcode`` or ``Pillow`` are not installed.
    """
    try:
        import qrcode  # type: ignore[import]
    except ModuleNotFoundError as exc:
        raise KSeFCryptoError("qrcode is not installed. Install it with: pip install ksef[qr]") from exc

    url = build_qr_code_1_url(
        environment=environment,
        invoice_date=invoice_date,
        seller_nip=seller_nip,
        file_sha256_b64url=file_sha256_b64url,
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")
