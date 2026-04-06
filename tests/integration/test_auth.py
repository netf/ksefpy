"""Integration tests for authentication — proving that AsyncKSeF authenticates correctly."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeF
from ksef.result import InvoiceResult
from ksef.testing import generate_test_invoice_xml

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_send_invoice_proves_auth(client: AsyncKSeF, nip: str):
    """Sending an invoice requires authentication — if this works, auth works."""
    xml = generate_test_invoice_xml(nip)
    result = await client.send_invoice(xml)
    assert isinstance(result, InvoiceResult)
    assert result.reference_number


async def test_constructor_rejects_empty_nip():
    """AsyncKSeF should raise ValueError when nip is empty."""
    with pytest.raises(ValueError, match="nip is required"):
        AsyncKSeF(nip="", token="some-token", env="test")


async def test_constructor_rejects_token_and_cert():
    """AsyncKSeF should raise ValueError when both token and cert are provided."""
    with pytest.raises(ValueError, match="either token OR"):
        AsyncKSeF(nip="1234567890", token="tok", cert=b"cert", key=b"key", env="test")


async def test_constructor_rejects_no_credentials():
    """AsyncKSeF should raise ValueError when no credentials are provided."""
    with pytest.raises(ValueError, match="Provide token or"):
        AsyncKSeF(nip="1234567890", env="test")


async def test_constructor_rejects_cert_without_key():
    """AsyncKSeF should raise ValueError when cert is provided without key."""
    with pytest.raises(ValueError, match="cert.*key|token"):
        AsyncKSeF(nip="1234567890", cert=b"cert", env="test")
