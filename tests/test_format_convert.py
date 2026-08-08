# -*- coding: utf-8 -*-
"""格式转换模块测试"""
import os
import sys
import tempfile
import pytest

# 确保项目根目录在 path 中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from engines.document import ParsedDocument, Chapter
from engines.importer import get_reader, read_document, get_supported_formats
from engines.importer.pdf_reader import PDFReader
from engines.importer.epub_reader import EPUBReader
from engines.importer.txt_reader import TXTReader
from engines.importer.mobi_reader import MOBIReader
from engines.exporters import get_exporter, export_document
from engines.export.txt_exporter import TXTExporter
from engines.export.epub_exporter import EPUBExporter
from engines.export.pdf_exporter import PDFExporter
from core.format_pipeline import FormatPipeline
from core.format_converter import FormatConverterService
from app.format_constants import (
    SUPPORTED_FORMATS, FORMAT_CONVERSION_MATRIX, FORMAT_LABELS,
    DEFAULT_EXPORT_OPTIONS
)


# ========== 文档模型测试 ==========

class TestParsedDocument:
    """统一文档模型测试"""

    def test_create_empty(self):
        doc = ParsedDocument()
        assert doc.title == ""
        assert doc.chapter_count == 0
        assert doc.total_chars == 0

    def test_add_chapter(self):
        doc = ParsedDocument(title="测试")
        ch = doc.add_chapter(title="第一章", paragraphs=["段落1", "段落2"])
        assert doc.chapter_count == 1
        assert ch.title == "第一章"
        assert len(ch.paragraphs) == 2

    def test_compute_stats(self):
        doc = ParsedDocument()
        doc.add_chapter(title="第一章", paragraphs=["abc", "de"])
        doc.add_chapter(title="第二章", paragraphs=["fghij"])
        assert doc.compute_stats() == 10
        assert doc.total_chars == 10

    def test_empty_chapters(self):
        doc = ParsedDocument(title="空书")
        assert doc.chapter_count == 0
        assert doc.total_chars == 0
        assert doc.compute_stats() == 0

    def test_chapter_with_images(self):
        doc = ParsedDocument()
        ch = doc.add_chapter(title="图文章节", paragraphs=["文字"])
        ch.images.append(b"\x89PNG")
        assert len(ch.images) == 1


# ========== 读取器测试 ==========

class TestReaders:
    """读取器注册和基础功能测试"""

    def test_get_reader_pdf(self):
        reader = get_reader("test.pdf")
        assert isinstance(reader, PDFReader)

    def test_get_reader_epub(self):
        reader = get_reader("test.epub")
        assert isinstance(reader, EPUBReader)

    def test_get_reader_txt(self):
        reader = get_reader("test.txt")
        assert isinstance(reader, TXTReader)

    def test_get_reader_mobi(self):
        reader = get_reader("test.mobi")
        assert isinstance(reader, MOBIReader)

    def test_get_reader_unsupported(self):
        with pytest.raises(ValueError, match="不支持"):
            get_reader("test.docx")

    def test_supported_formats(self):
        formats = get_supported_formats()
        assert "pdf" in formats
        assert "epub" in formats
        assert "txt" in formats
        assert "mobi" in formats


class TestTXTReader:
    """TXT 读取器测试"""

    def test_read_utf8(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("第一章 开始\n这是正文内容。\n第二章 结束\n这是第二章。", encoding="utf-8")

        reader = TXTReader()
        doc = reader.read(str(txt_file))

        assert doc.source_format == "txt"
        assert doc.title == "test"
        assert doc.chapter_count >= 2
        assert doc.total_chars > 0

    def test_read_gbk(self, tmp_path):
        txt_file = tmp_path / "test_gbk.txt"
        txt_file.write_text("第一章 测试\n正文。", encoding="gbk")

        reader = TXTReader()
        doc = reader.read(str(txt_file))

        assert doc.source_format == "txt"
        assert doc.chapter_count >= 1
        assert "正文" in doc.chapters[-1].paragraphs[0]

    def test_read_no_chapters(self, tmp_path):
        txt_file = tmp_path / "plain.txt"
        txt_file.write_text("这只是一段普通文本，没有章节标记。\n第二行文本。", encoding="utf-8")

        reader = TXTReader()
        doc = reader.read(str(txt_file))

        assert doc.chapter_count >= 1
        assert doc.total_chars > 0


# ========== 导出器测试 ==========

class TestExporters:
    """导出器注册和功能测试"""

    def test_get_exporter_txt(self):
        exporter = get_exporter("txt")
        assert isinstance(exporter, TXTExporter)

    def test_get_exporter_epub(self):
        exporter = get_exporter("epub")
        assert isinstance(exporter, EPUBExporter)

    def test_get_exporter_pdf(self):
        exporter = get_exporter("pdf")
        assert isinstance(exporter, PDFExporter)

    def test_get_exporter_mobi_not_supported(self):
        """MOBI 导出不支持"""
        with pytest.raises(ValueError, match="不支持"):
            get_exporter("mobi")

    def test_get_exporter_unsupported(self):
        with pytest.raises(ValueError, match="不支持"):
            get_exporter("docx")


class TestTXTExporter:
    """TXT 导出器测试"""

    def test_export_basic(self, tmp_path):
        doc = ParsedDocument(title="测试书", author="作者")
        doc.add_chapter(title="第一章", paragraphs=["段落1", "段落2"])
        doc.add_chapter(title="第二章", paragraphs=["段落3"])

        output = str(tmp_path / "output.txt")
        exporter = TXTExporter()
        result = exporter.export(doc, output)

        assert result == output
        assert os.path.exists(output)

        with open(output, "r", encoding="utf-8") as f:
            content = f.read()
        assert "测试书" in content
        assert "第一章" in content
        assert "段落1" in content
        assert "段落2" in content
        assert "第二章" in content

    def test_export_empty_doc(self, tmp_path):
        doc = ParsedDocument()
        output = str(tmp_path / "empty.txt")
        exporter = TXTExporter()
        result = exporter.export(doc, output)

        assert os.path.exists(output)


class TestEPUBExporter:
    """EPUB 导出器测试"""

    def test_export_basic(self, tmp_path):
        doc = ParsedDocument(title="测试书", author="作者")
        doc.add_chapter(title="第一章", paragraphs=["段落1", "段落2"])
        doc.add_chapter(title="第二章", paragraphs=["段落3"])

        output = str(tmp_path / "output.epub")
        exporter = EPUBExporter()
        result = exporter.export(doc, output, options={"theme": "classic"})

        assert result == output
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0


class TestPDFExporter:
    """PDF 导出器测试"""

    def test_export_basic(self, tmp_path):
        doc = ParsedDocument(title="测试书", author="作者")
        doc.add_chapter(title="第一章", paragraphs=["段落1", "段落2"])

        output = str(tmp_path / "output.pdf")
        exporter = PDFExporter()
        result = exporter.export(doc, output)

        assert result == output
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0


# ========== Pipeline 测试 ==========

class TestFormatPipeline:
    """格式转换 Pipeline 测试"""

    def test_txt_to_epub(self, tmp_path):
        """TXT → EPUB"""
        txt_file = tmp_path / "input.txt"
        txt_file.write_text("第一章 测试\n这是正文。\n第二章 测试二\n第二章正文。", encoding="utf-8")

        output = str(tmp_path / "output.epub")
        pipeline = FormatPipeline()
        report = pipeline.run(str(txt_file), "epub", output)

        assert report["source_format"] == "txt"
        assert report["target_format"] == "epub"
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0

    def test_txt_to_pdf(self, tmp_path):
        """TXT → PDF"""
        txt_file = tmp_path / "input.txt"
        txt_file.write_text("第一章 测试\n这是正文。", encoding="utf-8")

        output = str(tmp_path / "output.pdf")
        pipeline = FormatPipeline()
        report = pipeline.run(str(txt_file), "pdf", output)

        assert report["source_format"] == "txt"
        assert report["target_format"] == "pdf"
        assert os.path.exists(output)

    def test_epub_to_txt(self, tmp_path):
        """EPUB → TXT"""
        # 先创建一个 EPUB
        doc = ParsedDocument(title="测试书", author="作者")
        doc.add_chapter(title="第一章", paragraphs=["段落1", "段落2"])

        epub_file = str(tmp_path / "input.epub")
        EPUBExporter().export(doc, epub_file)

        # 再转 TXT
        output = str(tmp_path / "output.txt")
        pipeline = FormatPipeline()
        report = pipeline.run(epub_file, "txt", output)

        assert report["source_format"] == "epub"
        assert report["target_format"] == "txt"
        assert os.path.exists(output)

        with open(output, "r", encoding="utf-8") as f:
            content = f.read()
        assert "段落1" in content or "段落2" in content

    def test_cancel(self):
        """测试取消"""
        pipeline = FormatPipeline()
        pipeline.cancel()
        assert pipeline._cancelled is True


# ========== 服务层测试 ==========

class TestFormatConverterService:
    """格式转换服务层测试"""

    def test_get_supported_targets(self):
        service = FormatConverterService()
        targets = service.get_supported_targets("pdf")
        assert "epub" in targets
        assert "txt" in targets
        assert "mobi" not in targets  # MOBI 不可作为导出目标
        assert "pdf" not in targets  # 不能转自己

    def test_get_supported_targets_txt(self):
        service = FormatConverterService()
        targets = service.get_supported_targets("txt")
        assert "epub" in targets
        assert "pdf" in targets

    def test_create_task(self):
        service = FormatConverterService()
        task_id = service.create_task("test.pdf", "epub", "output.epub")
        assert task_id >= 10000
        info = service.get_task_info(task_id)
        assert info["source_path"] == "test.pdf"
        assert info["target_format"] == "epub"
        assert info["status"] == "pending"

    def test_list_tasks(self):
        service = FormatConverterService()
        service.create_task("a.pdf", "epub")
        service.create_task("b.txt", "pdf")
        tasks = service.list_tasks()
        assert len(tasks) >= 2


# ========== 常量测试 ==========

class TestFormatConstants:
    """格式常量测试"""

    def test_supported_formats(self):
        assert set(SUPPORTED_FORMATS) == {"pdf", "epub", "txt", "mobi"}

    def test_conversion_matrix(self):
        # PDF/EPUB/TXT 可互转，MOBI 只能读取不能导出
        for src, targets in FORMAT_CONVERSION_MATRIX.items():
            assert src not in targets
            if src == "mobi":
                assert len(targets) == 3  # MOBI 可转 3 种
            else:
                assert len(targets) == 2  # 其他格式可转 2 种（不含 MOBI）
            assert "mobi" not in targets  # 任何格式都不能转为 MOBI

    def test_format_labels(self):
        for fmt in SUPPORTED_FORMATS:
            assert fmt in FORMAT_LABELS

    def test_default_options(self):
        for fmt in SUPPORTED_FORMATS:
            assert fmt in DEFAULT_EXPORT_OPTIONS


# ========== 端到端测试 ==========

class TestEndToEnd:
    """端到端格式转换测试"""

    def test_txt_to_epub_to_txt(self, tmp_path):
        """TXT → EPUB → TXT 往返"""
        original_text = "第一章 开始\n这是第一章的正文内容。\n第二章 继续\n这是第二章的内容。"
        txt_file = tmp_path / "original.txt"
        txt_file.write_text(original_text, encoding="utf-8")

        # TXT → EPUB
        epub_path = str(tmp_path / "converted.epub")
        pipeline = FormatPipeline()
        report1 = pipeline.run(str(txt_file), "epub", epub_path)
        assert os.path.exists(epub_path)

        # EPUB → TXT
        txt2_path = str(tmp_path / "roundtrip.txt")
        report2 = pipeline.run(epub_path, "txt", txt2_path)
        assert os.path.exists(txt2_path)

        # 验证内容保留
        with open(txt2_path, "r", encoding="utf-8") as f:
            converted_text = f.read()
        assert "第一章的正文内容" in converted_text or "正文内容" in converted_text
