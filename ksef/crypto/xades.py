"""XAdES XML signing service (requires the [xades] optional extra)."""

from __future__ import annotations

from ksef.exceptions import KSeFCryptoError


class XAdESService:
    """Sign XML documents using XAdES enveloped signatures.

    Requires ``signxml`` to be installed::

        pip install ksef[xades]
    """

    def sign(
        self,
        xml_document: str,
        *,
        certificate: bytes,
        private_key: bytes,
    ) -> str:
        """Return *xml_document* with an enveloped XAdES/XML-DSig signature.

        Parameters
        ----------
        xml_document:
            Well-formed XML string to sign.
        certificate:
            PEM-encoded X.509 certificate (bytes).
        private_key:
            PEM-encoded private key (bytes).

        Raises
        ------
        KSeFCryptoError
            If ``signxml`` is not installed or signing fails.
        """
        try:
            from signxml import XMLSigner, methods  # type: ignore[import]
        except ModuleNotFoundError as exc:
            raise KSeFCryptoError(
                "signxml is not installed. Install it with: pip install ksef[xades]"
            ) from exc

        try:
            from lxml import etree  # type: ignore[import]

            root = etree.fromstring(xml_document.encode())

            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
            )

            signed_root = signer.sign(
                root,
                key=private_key,
                cert=certificate,
            )

            return etree.tostring(signed_root, encoding="unicode")
        except KSeFCryptoError:
            raise
        except Exception as exc:
            raise KSeFCryptoError(f"XAdES signing failed: {exc}") from exc
