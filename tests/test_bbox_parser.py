# -*- coding: utf-8 -*-
"""BBox 解析器单元测试"""
import pytest
from engines.ocr.base import OCRBlock
from engines.layout.bbox_parser import BBoxParser


class TestBBoxParser:

    @pytest.fixture
    def parser(self):
        return BBoxParser()

    def test_parse_empty(self, parser):
        assert parser.parse(None) == []
        assert parser.parse((None, 0)) == []
        assert parser.parse(([], 0)) == []

    def test_parse_basic(self, parser):
        """基本解析"""
        raw = ([
            [[[100, 100], [300, 100], [300, 140], [100, 140]], "第一行", 0.95],
            [[[100, 200], [400, 200], [400, 240], [100, 240]], "第二行", 0.88],
        ], 0.1)
        blocks = parser.parse(raw)
        assert len(blocks) == 2
        assert blocks[0].text == "第一行"
        assert blocks[0].confidence == 0.95
        assert blocks[1].text == "第二行"

    def test_parse_sorted_by_y(self, parser):
        """结果应按 Y 坐标排序"""
        raw = ([
            [[[100, 300], [300, 300], [300, 340], [100, 340]], "第三行", 0.9],
            [[[100, 100], [300, 100], [300, 140], [100, 140]], "第一行", 0.9],
            [[[100, 200], [300, 200], [300, 240], [100, 240]], "第二行", 0.9],
        ], 0.1)
        blocks = parser.parse(raw)
        assert blocks[0].text == "第一行"
        assert blocks[1].text == "第二行"
        assert blocks[2].text == "第三行"

    def test_parse_skip_empty(self, parser):
        """跳过空文本"""
        raw = ([
            [[[100, 100], [300, 100], [300, 140], [100, 140]], "有文字", 0.9],
            [[[100, 200], [300, 200], [300, 240], [100, 240]], "", 0.5],
            [[[100, 300], [300, 300], [300, 340], [100, 340]], "  ", 0.5],
        ], 0.1)
        blocks = parser.parse(raw)
        assert len(blocks) == 1
        assert blocks[0].text == "有文字"

    def test_parse_page_size(self, parser):
        """推断页面尺寸"""
        raw = ([
            [[[100, 100], [800, 100], [800, 140], [100, 140]], "A", 0.9],
            [[[100, 200], [900, 200], [900, 240], [100, 240]], "B", 0.9],
        ], 0.1)
        blocks = parser.parse(raw)
        page_w, page_h = parser.parse_page_size(blocks)
        assert page_w == 900
        assert page_h == 240

    def test_parse_page_size_empty(self, parser):
        """空 blocks 的页面尺寸"""
        page_w, page_h = parser.parse_page_size([])
        assert page_w == 0
        assert page_h == 0

    def test_block_properties(self, parser):
        """OCRBlock 属性正确性"""
        raw = ([
            [[[100, 100], [300, 100], [300, 140], [100, 140]], "test", 0.9],
        ], 0.1)
        blocks = parser.parse(raw)
        b = blocks[0]
        assert b.x_left == 100
        assert b.x_right == 300
        assert b.x_center == 200
        assert b.y_top == 100
        assert b.y_bot == 140
        assert b.height == 40
        assert b.width == 200
