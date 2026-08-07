# -*- coding: utf-8 -*-
"""PDF 分析器单元测试"""
import os
import tempfile
import pytest
import fitz
from engines.pdf.analyzer import PDFAnalyzer


class TestPDFAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return PDFAnalyzer()

    @pytest.fixture
    def sample_pdf(self):
        """创建一个简单的测试 PDF"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "Hello World 测试文字 " * 10)
        doc.save(path)
        doc.close()
        yield path
        os.unlink(path)

    def test_analyze_text_pdf(self, analyzer, sample_pdf):
        info = analyzer.analyze(sample_pdf)
        assert info["pages"] == 1
        assert info["type"] in ("text", "mixed")
        assert "file_size" in info
        assert "has_toc" in info

    def test_analyze_returns_required_fields(self, analyzer, sample_pdf):
        """分析结果必须包含所有必需字段"""
        info = analyzer.analyze(sample_pdf)
        required_keys = {"pages", "type", "text_pages", "image_pages",
                         "page_size", "file_size", "has_toc"}
        assert required_keys.issubset(info.keys())

    def test_analyze_page_size(self, analyzer, sample_pdf):
        """页面尺寸应该是正数"""
        info = analyzer.analyze(sample_pdf)
        assert info["page_size"][0] > 0
        assert info["page_size"][1] > 0

    def test_analyze_estimated_time(self, analyzer, sample_pdf):
        """应该包含预计耗时"""
        info = analyzer.analyze(sample_pdf)
        assert "estimated_time" in info
        assert len(info["estimated_time"]) > 0

    def test_analyze_toc(self, analyzer, sample_pdf):
        """应该返回 toc 列表"""
        info = analyzer.analyze(sample_pdf)
        assert "toc" in info
        assert isinstance(info["toc"], list)

    def test_analyze_empty_pdf(self, analyzer):
        """空白 PDF（1页无文字）"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        doc = fitz.open()
        doc.new_page()  # 空白页，无文字
        doc.save(path)
        doc.close()
        try:
            info = analyzer.analyze(path)
            assert info["pages"] == 1
            assert info["type"] in ("scan", "mixed", "unknown")
        finally:
            os.unlink(path)
