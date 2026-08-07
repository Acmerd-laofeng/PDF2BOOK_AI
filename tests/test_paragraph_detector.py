# -*- coding: utf-8 -*-
"""段落检测器单元测试"""
import pytest
from engines.ocr.base import OCRBlock
from engines.layout.paragraph_detector import ParagraphDetector


def make_block(text: str, x0: float, y0: float, x1: float, y1: float) -> OCRBlock:
    """构造 OCRBlock"""
    return OCRBlock(
        text=text,
        bbox=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
        confidence=0.95,
    )


class TestParagraphDetector:

    @pytest.fixture
    def detector(self):
        return ParagraphDetector()

    def test_empty_input(self, detector):
        assert detector.detect([]) == []

    def test_single_line(self, detector):
        blocks = [make_block("这是一行文字", 100, 100, 500, 140)]
        result = detector.detect(blocks)
        assert len(result) == 1
        assert result[0][0] == 'body'
        assert result[0][1] == "这是一行文字"

    def test_indent_creates_new_paragraph(self, detector):
        blocks = [
            make_block("第一段内容第一段内容", 100, 100, 600, 140),
            make_block("第二段开始", 150, 200, 400, 240),  # 缩进 50 > 30
        ]
        result = detector.detect(blocks)
        assert len(result) == 2

    def test_page_number_filtered(self, detector):
        blocks = [
            make_block("正文内容", 100, 100, 500, 140),
            make_block("123", 400, 2400, 440, 2440),  # 底部纯数字
        ]
        result = detector.detect(blocks)
        assert len(result) == 1
        assert "123" not in result[0][1]

    def test_centered_short_is_heading(self, detector):
        # 页面宽度 1000，居中 x_center=500
        blocks = [
            make_block("正文内容正文内容正文内容正文内容", 100, 100, 900, 140),  # 宽行做参考
            make_block("第一章", 450, 200, 550, 240),  # 居中，短
        ]
        result = detector.detect(blocks)
        assert len(result) == 2
        assert result[1][0] == 'heading'

    def test_cross_page_merge(self, detector):
        detector.merge_cross_page = True
        paragraphs = [
            ('body', "这是一段没有句末标点的文字继续到下一页"),
            ('body', "的内容到这里结束。"),
        ]
        result = detector.postprocess(paragraphs)
        # 应该合并为一段
        assert len(result) == 1
        assert "。" in result[0][1]
