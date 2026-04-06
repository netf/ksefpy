"""XML serialization and deserialization helpers using xsdata."""

from __future__ import annotations

import dataclasses
import xml.etree.ElementTree as ET
from typing import TypeVar

from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser as _XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from ksef.exceptions import KSeFXmlError

T = TypeVar("T")

_context = XmlContext()
_serializer = XmlSerializer(
    context=_context,
    config=SerializerConfig(pretty_print=False, encoding="UTF-8"),
)


def _has_xsdata_metadata(cls: type) -> bool:
    """Return True if *cls* has at least one field with xsdata-style metadata."""
    if not dataclasses.is_dataclass(cls):
        return False
    return any("type" in f.metadata for f in dataclasses.fields(cls))  # type: ignore[arg-type]


def _et_deserialize(xml_bytes: bytes, target_class: type[T]) -> T:
    """Deserialize *xml_bytes* into *target_class* using stdlib ElementTree.

    This handles plain dataclasses that lack xsdata ``field(metadata=...)``
    annotations by mapping child element text by local name.
    """
    root = ET.fromstring(xml_bytes.decode())
    tag = root.tag
    ns_prefix = ""
    if tag.startswith("{"):
        ns_prefix = "{" + tag[1 : tag.index("}")] + "}"

    kwargs: dict[str, object] = {}
    hints = {f.name: f.type for f in dataclasses.fields(target_class)}  # type: ignore[arg-type]
    for child in root:
        local = child.tag.replace(ns_prefix, "")
        if local in hints:
            kwargs[local] = child.text or ""

    return target_class(**kwargs)  # type: ignore[call-arg]


def serialize_to_xml(obj: object) -> bytes:
    """Serialize a dataclass instance to XML bytes.

    Parameters
    ----------
    obj:
        An xsdata-compatible dataclass (must have a ``Meta`` inner class).

    Returns
    -------
    bytes
        UTF-8 encoded XML document.

    Raises
    ------
    KSeFXmlError
        If serialization fails.
    """
    try:
        xml_str = _serializer.render(obj)
        return xml_str.encode("UTF-8")
    except Exception as exc:
        raise KSeFXmlError(f"XML serialization failed: {exc}") from exc


def deserialize_from_xml(xml_bytes: bytes, target_class: type[T]) -> T:
    """Deserialize XML bytes into an instance of *target_class*.

    For xsdata-generated classes (with ``field(metadata={...})`` annotations)
    this delegates to the full xsdata ``XmlParser``.  For plain dataclasses
    it falls back to a lightweight ``xml.etree.ElementTree`` mapper.

    Parameters
    ----------
    xml_bytes:
        Raw XML document bytes.
    target_class:
        The dataclass type to parse into.

    Returns
    -------
    T
        Populated instance of *target_class*.

    Raises
    ------
    KSeFXmlError
        If deserialization fails.
    """
    try:
        if _has_xsdata_metadata(target_class):
            ctx = XmlContext()
            parser = _XmlParser(
                context=ctx,
                config=ParserConfig(fail_on_unknown_properties=False),
            )
            return parser.from_bytes(xml_bytes, target_class)
        # Plain dataclass without xsdata metadata — use stdlib ET mapper.
        return _et_deserialize(xml_bytes, target_class)
    except KSeFXmlError:
        raise
    except Exception as exc:
        raise KSeFXmlError(f"XML deserialization failed: {exc}") from exc
