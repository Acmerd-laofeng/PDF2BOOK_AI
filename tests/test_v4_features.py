# -*- coding: utf-8 -*-
"""v4.0 新功能测试

测试内容：
1. 章节检测增强（正则扩展、层级目录、多信号评分）
2. 图片提取器（ImageExtractor 初始化和方法签名）
3. EPUB 图片嵌入（build() 接受 images 参数）
4. 纠错报告生成（find_low_confidence_words + generate_correction_report）
5. 并行 OCR 引擎（ParallelOcrEngine 初始化）
6. 常量更新（CHAPTER_PATTERNS 扩展、版本号）
"""
import os
import sys
import json
import tempfile
from pathlib import Path

# 确保项目根在 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest


class TestChapterDetectorV4:
    """章节检测器 v4 测试"""

    def setup_method(self):
        from engines.layout.chapter_detector import ChapterDetector
        self.detector = ChapterDetector()

    def test_enhanced_regex_patterns(self):
        """测试扩展正则"""
        # 原有正则
        assert self.detector._is_chapter_title("第一章 风起云涌")
        assert self.detector._is_chapter_title("第3回 对决")
        assert self.detector._is_chapter_title("Chapter 5")
        assert self.detector._is_chapter_title("序")
        assert self.detector._is_chapter_title("后记")
        assert self.detector._is_chapter_title("附录A")

    def test_new_regex_patterns(self):
        """测试新增正则"""
        # 楔子、番外、引子、终章、序章
        assert self.detector._is_chapter_title("楔子")
        assert self.detector._is_chapter_title("番外")
        assert self.detector._is_chapter_title("番外篇")
        assert self.detector._is_chapter_title("引子")
        assert self.detector._is_chapter_title("终章")
        assert self.detector._is_chapter_title("序章")
        assert self.detector._is_chapter_title("跋")
        assert self.detector._is_chapter_title("后序")
        assert self.detector._is_chapter_title("尾声")

    def test_volume_patterns(self):
        """测试卷/部检测"""
        assert self.detector._is_chapter_title("上卷")
        assert self.detector._is_chapter_title("中卷")
        assert self.detector._is_chapter_title("下卷")
        assert self.detector._is_chapter_title("上部")
        assert self.detector._is_chapter_title("卷一")
        assert self.detector._is_chapter_title("第一卷")

    def test_chapter_with_subtitle(self):
        """带副标题的章节"""
        assert self.detector._is_chapter_title("第一章 风起云涌")
        assert self.detector._is_chapter_title("第三章 黄昏之战")
        assert self.detector._is_chapter_title("Chapter 5 The Beginning")

    def test_detect_level(self):
        """测试层级检测"""
        assert self.detector._detect_level("第一卷 天下") == 1
        assert self.detector._detect_level("上卷") == 1
        assert self.detector._detect_level("卷一") == 1
        assert self.detector._detect_level("第一章 风起") == 2
        assert self.detector._detect_level("Chapter 5") == 2
        assert self.detector._detect_level("第三节 小节") == 3
        assert self.detector._detect_level("一、引言") == 3
        assert self.detector._detect_level("序") == 2
        assert self.detector._detect_level("后记") == 2

    def test_detect_with_level(self):
        """测试层级目录生成"""
        paragraphs = [
            ('heading', '第一卷 天下'),
            ('body', '这是内容...'),
            ('heading', '第一章 风起'),
            ('body', '章节内容...'),
            ('heading', '第三节 细节'),
            ('body', '小节内容...'),
        ]
        result = self.detector.detect_with_level(paragraphs)
        assert result[0] == ('heading', '第一卷 天下', 1)
        assert result[2] == ('heading', '第一章 风起', 2)
        assert result[4] == ('heading', '第三节 细节', 3)

    def test_extract_chapters_with_level(self):
        """测试带层级的章节提取"""
        paragraphs = [
            ('heading', '第一卷 天下', 1),
            ('body', '内容1', 0),
            ('heading', '第一章 风起', 2),
            ('body', '内容2', 0),
            ('heading', '第三节 细节', 3),
            ('body', '内容3', 0),
        ]
        chapters = self.detector.extract_chapters_with_level(paragraphs)
        assert len(chapters) == 3
        assert chapters[0]["title"] == "第一卷 天下"
        assert chapters[0]["level"] == 1
        assert chapters[1]["title"] == "第一章 风起"
        assert chapters[1]["level"] == 2
        assert chapters[2]["title"] == "第三节 细节"
        assert chapters[2]["level"] == 3

    def test_detect_enhanced_context_signals(self):
        """测试上下文信号"""
        paragraphs = [
            ('body', '这是正文内容部分。'),
            ('body', '第一章 风起'),  # 有正则匹配，直接通过
            ('body', '这是正文内容部分。'),
        ]
        # 无间距信息，但正则匹配应该直接通过
        result = self.detector.detect_enhanced(paragraphs)
        assert result[1] == ('heading', '第一章 风起')

    def test_detect_enhanced_with_gaps(self):
        """测试带间距的增强检测"""
        paragraphs = [
            ('body', '正文段落一。'),
            ('body', '风起'),  # 短文本无标点
            ('body', '正文段落二。'),
        ]
        gaps = [0, 50, 5]  # 前有大间距
        avg_height = 20

        result = self.detector.detect_enhanced(paragraphs, avg_height, gaps)
        # "风起" 短文本无标点 + 前有大间距 + 后无大间距 = 2 分
        # 应该被标记为 heading
        assert result[1] == ('heading', '风起')

    def test_non_chapter_text(self):
        """非章节标题不应被误判"""
        assert not self.detector._is_chapter_title("这是正文内容，有逗号，有句号。")
        assert not self.detector._is_chapter_title("很长的标题文本超过了五十个字符的限制应该不被识别为标题" * 2)
        assert not self.detector._is_chapter_title("")


class TestImageExtractor:
    """图片提取器测试"""

    def test_init(self):
        from engines.pdf.image_extractor import ImageExtractor
        extractor = ImageExtractor()
        assert extractor.min_width == 100
        assert extractor.min_height == 100

    def test_init_custom_params(self):
        from engines.pdf.image_extractor import ImageExtractor
        extractor = ImageExtractor(min_width=200, min_height=200)
        assert extractor.min_width == 200
        assert extractor.min_height == 200

    def test_extract_from_nonexistent_pdf(self):
        """不存在的 PDF 应该抛出异常"""
        from engines.pdf.image_extractor import ImageExtractor
        extractor = ImageExtractor()
        import fitz
        with pytest.raises(Exception):
            doc = fitz.open("nonexistent.pdf")
            extractor.extract_from_page(doc, 0)


class TestEpubBuilderImages:
    """EPUB 图片嵌入测试"""

    def test_build_accepts_images_param(self):
        """build() 应该接受 images 参数"""
        from engines.export.epub import EPUBBuilder
        import inspect
        sig = inspect.signature(EPUBBuilder.build)
        assert 'images' in sig.parameters
        assert sig.parameters['images'].default is None

    def test_build_with_images(self):
        """测试带图片的 EPUB 生成"""
        from engines.export.epub import EPUBBuilder

        # 创建一个最小的 PNG 图片 (1x1 红色像素)
        import struct
        import zlib

        def make_minimal_png():
            # 最小 PNG: 1x1 红色像素
            width, height = 1, 1
            # PNG signature
            sig = b'\x89PNG\r\n\x1a\n'
            # IHDR chunk
            ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
            ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc & 0xffffffff)
            # IDAT chunk
            raw_data = b'\x00\xff\x00\x00'  # filter byte + RGB
            compressed = zlib.compress(raw_data)
            idat_crc = zlib.crc32(b'IDAT' + compressed)
            idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc & 0xffffffff)
            # IEND chunk
            iend_crc = zlib.crc32(b'IEND')
            iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc & 0xffffffff)
            return sig + ihdr + idat + iend

        img_bytes = make_minimal_png()
        images = [{
            "image_bytes": img_bytes,
            "ext": "png",
            "width": 1,
            "height": 1,
            "page": 0,
            "index": 0,
        }]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_with_images.epub")
            builder = EPUBBuilder()
            paragraphs = [
                ('heading', '测试章节'),
                ('body', '这是正文。'),
            ]
            result = builder.build(
                paragraphs=paragraphs,
                title="测试图片EPUB",
                author="测试",
                output_path=output_path,
                theme="classic",
                images=images,
            )
            assert os.path.exists(output_path)
            assert result["image_count"] == 1
            assert result["chapter_count"] >= 1


class TestCorrectorV4:
    """纠错器 v4 测试"""

    def test_find_low_confidence_words(self):
        from engines.ai.corrector import Corrector
        corrector = Corrector()
        corrector._dictionary = {"商稻": "商務", "春苑": "春秋"}

        text = "商稻春秋是一本书，春苑也是。"
        findings = corrector.find_low_confidence_words(text)

        # 应该找到 "商稻" 和 "春苑"
        words_found = [f["word"] for f in findings]
        assert "商稻" in words_found
        assert "春苑" in words_found

    def test_find_confusable_chars(self):
        from engines.ai.corrector import Corrector
        corrector = Corrector()
        # 不在字典中的形似字
        text = "已己巳三个字容易混淆"
        findings = corrector.find_low_confidence_words(text)
        confusable = [f for f in findings if f["type"] == "confusable"]
        # "己" 是常见形似字
        words_found = [f["word"] for f in confusable]
        assert "己" in words_found

    def test_generate_correction_report(self):
        from engines.ai.corrector import Corrector
        corrector = Corrector()
        corrector._dictionary = {"商稻": "商務"}

        paragraphs = [
            ('body', '商稻是一本好书。'),
            ('body', '正文内容正常。'),
        ]
        report = corrector.generate_correction_report(paragraphs)
        assert report["total_findings"] >= 1
        assert report["known_corrections"] >= 1
        assert len(report["details"]) >= 1
        assert report["details"][0]["word"] == "商稻"
        assert report["details"][0]["suggestion"] == "商務"

    def test_correction_report_empty(self):
        from engines.ai.corrector import Corrector
        corrector = Corrector()
        paragraphs = [('body', '完全正常的文本。')]
        report = corrector.generate_correction_report(paragraphs)
        assert report["total_findings"] == 0


class TestParallelOcrEngine:
    """并行 OCR 引擎测试"""

    def test_init(self):
        from core.parallel_ocr import ParallelOcrEngine
        engine = ParallelOcrEngine(thread_count=4)
        assert engine.thread_count == 4
        assert engine.pool.maxThreadCount() == 4

    def test_init_custom_threads(self):
        from core.parallel_ocr import ParallelOcrEngine
        engine = ParallelOcrEngine(thread_count=8)
        assert engine.thread_count == 8
        assert engine.pool.maxThreadCount() == 8

    def test_cancel(self):
        from core.parallel_ocr import ParallelOcrEngine
        engine = ParallelOcrEngine()
        engine.cancel()
        assert engine._cancelled is True


class TestConstantsV4:
    """常量更新测试"""

    def test_version_4(self):
        from app.constants import APP_VERSION
        assert APP_VERSION == "4.0.7"

    def test_chapter_patterns_expanded(self):
        from app.constants import CHAPTER_PATTERNS
        import re

        patterns = [re.compile(p) for p in CHAPTER_PATTERNS]

        # 测试新增模式匹配
        test_cases = [
            "楔子", "番外", "番外篇", "引子", "终章", "序章",
            "跋", "后序", "尾声",
            "上卷", "中卷", "下卷", "上部", "卷一", "第一卷",
        ]
        for text in test_cases:
            matched = any(p.match(text) for p in patterns)
            assert matched, f"正则应匹配: {text}"

    def test_chapter_patterns_still_match_old(self):
        from app.constants import CHAPTER_PATTERNS
        import re

        patterns = [re.compile(p) for p in CHAPTER_PATTERNS]
        old_cases = [
            "第一章", "第3回", "Chapter 5", "序", "后记", "附录A",
        ]
        for text in old_cases:
            matched = any(p.match(text) for p in patterns)
            assert matched, f"原有正则应仍匹配: {text}"


class TestPipelineV4Integration:
    """Pipeline v4 集成测试"""

    def test_pipeline_has_image_extractor(self):
        from core.pipeline import Pipeline
        from engines.pdf.image_extractor import ImageExtractor
        p = Pipeline()
        assert hasattr(p, 'image_extractor')
        assert isinstance(p.image_extractor, ImageExtractor)

    def test_pipeline_report_has_correction_report(self):
        """Pipeline 返回报告应包含 correction_report 字段"""
        from core.pipeline import Pipeline
        import inspect
        src = inspect.getsource(Pipeline.run)
        assert 'correction_report' in src
        assert 'generate_correction_report' in src

    def test_pipeline_report_has_image_count(self):
        """Pipeline 返回报告应包含实际图片数量"""
        from core.pipeline import Pipeline
        import inspect
        src = inspect.getsource(Pipeline.run)
        assert 'extracted_images' in src
        assert 'enable_image_extract' in src


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
