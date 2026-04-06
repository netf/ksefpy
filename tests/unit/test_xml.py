from ksef.schemas import SchemaVersion
from ksef.xml import deserialize_from_xml, serialize_to_xml


def test_schema_version_enum():
    assert SchemaVersion.FA_3.value == "FA(3)"
    assert SchemaVersion.FA_2.value == "FA(2)"


def test_serialize_to_xml_bytes():
    from dataclasses import dataclass

    @dataclass
    class SimpleDoc:
        class Meta:
            name = "SimpleDoc"
            namespace = "http://test.example.com"
        value: str = ""

    doc = SimpleDoc(value="hello")
    xml_bytes = serialize_to_xml(doc)
    assert isinstance(xml_bytes, bytes)
    assert b"hello" in xml_bytes


def test_deserialize_from_xml():
    from dataclasses import dataclass

    @dataclass
    class SimpleDoc:
        class Meta:
            name = "SimpleDoc"
            namespace = "http://test.example.com"
        value: str = ""

    xml = b'<?xml version="1.0" encoding="UTF-8"?><SimpleDoc xmlns="http://test.example.com"><value>world</value></SimpleDoc>'
    doc = deserialize_from_xml(xml, SimpleDoc)
    assert doc.value == "world"
