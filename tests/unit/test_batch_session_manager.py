from ksef.coordinators.batch_session import BatchSessionContext


def test_batch_context_builds_zip():
    ctx = BatchSessionContext()
    ctx.add_invoice_xml(b"<Faktura>1</Faktura>")
    ctx.add_invoice_xml(b"<Faktura>2</Faktura>")

    zip_bytes = ctx._build_zip()
    assert len(zip_bytes) > 0

    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert len(names) == 2
        assert zf.read(names[0]) == b"<Faktura>1</Faktura>"
