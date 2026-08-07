# -*- coding: utf-8 -*-
"""PDF Reader/Renderer 单元测试"""
import os
import tempfile
import pytest
import fitz
from engines.pdf.reader import PDFReader
from engines.pdf.renderer import Renderer


class TestPDFReader:

    @pytest.fixture
    def sample_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), f"Page {i+1} 测试文字 " * 5)
        doc.save(path)
        doc.close()
        yield path
        os.unlink(path)

    def test_count(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            assert reader.count() == 3
            assert len(reader) == 3

    def test_get_page(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            page = reader.get_page(0)
            assert page is not None

    def test_get_page_out_of_range(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            with pytest.raises(IndexError):
                reader.get_page(10)

    def test_get_text(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            text = reader.get_text(0)
            assert "Page 1" in text

    def test_has_text_layer(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            assert reader.has_text_layer(0) == True

    def test_get_toc(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            toc = reader.get_toc()
            assert isinstance(toc, list)

    def test_get_page_size(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            w, h = reader.get_page_size()
            assert w > 0
            assert h > 0

    def test_context_manager(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            assert reader._doc is not None
        assert reader._doc is None

    def test_iterate(self, sample_pdf):
        with PDFReader(sample_pdf) as reader:
            pages = list(reader)
            assert len(pages) == 3


class TestRenderer:

    @pytest.fixture
    def sample_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test text 测试")
        doc.save(path)
        doc.close()
        yield path
        os.unlink(path)

    def test_render_pixmap(self, sample_pdf):
        renderer = Renderer()
        with PDFReader(sample_pdf) as reader:
            page = reader.get_page(0)
            pix = renderer.render(page, dpi=150)
            assert pix is not None
            assert pix.width > 0
            assert pix.height > 0

    def test_render_to_bytes(self, sample_pdf):
        renderer = Renderer()
        with PDFReader(sample_pdf) as reader:
            page = reader.get_page(0)
            img_bytes = renderer.render_to_bytes(page, dpi=150, fmt="png")
            assert len(img_bytes) > 0
            # PNG magic bytes
            assert img_bytes[:4] == b'\x89PNG'

    def test_render_to_file(self, sample_pdf):
        renderer = Renderer()
        with PDFReader(sample_pdf) as reader:
            page = reader.get_page(0)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                output = f.name
            try:
                renderer.render_to_file(page, output, dpi=150)
                assert os.path.exists(output)
                assert os.path.getsize(output) > 0
            finally:
                if os.path.exists(output):
                    os.unlink(output)

    def test_dpi_affects_size(self, sample_pdf):
        """更高 DPI 产生更大的图片"""
        renderer = Renderer()
        with PDFReader(sample_pdf) as reader:
            page = reader.get_page(0)
            pix_150 = renderer.render(page, dpi=150)
            pix_300 = renderer.render(page, dpi=300)
            assert pix_300.width > pix_150.width
            assert pix_300.height > pix_150.height

    def test_last_dpi(self, sample_pdf):
        renderer = Renderer()
        with PDFReader(sample_pdf) as reader:
            page = reader.get_page(0)
            renderer.render(page, dpi=250)
            assert renderer.last_dpi == 250
