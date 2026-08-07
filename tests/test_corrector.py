# -*- coding: utf-8 -*-
"""OCR 纠错器单元测试"""
import json
import os
import tempfile
import pytest
from engines.ai.corrector import Corrector


class TestCorrector:

    @pytest.fixture
    def corrector(self):
        c = Corrector()
        c._dictionary = {
            "商稻": "商務",
            "春苑": "春秋",
            "巳经": "已经",
        }
        return c

    def test_correct_single(self, corrector):
        text, count = corrector.correct("商稻春秋")
        assert text == "商務春秋"
        assert count == 1

    def test_correct_multiple(self, corrector):
        text, count = corrector.correct("商稻和春苑和巳经完成")
        assert "商務" in text
        assert "春秋" in text
        assert "已经" in text
        assert count == 3

    def test_correct_no_match(self, corrector):
        text, count = corrector.correct("这段文字没有错误")
        assert text == "这段文字没有错误"
        assert count == 0

    def test_correct_repeated(self, corrector):
        text, count = corrector.correct("商稻商稻商稻")
        assert text == "商務商務商務"
        assert count == 3

    def test_correct_paragraphs(self, corrector):
        paragraphs = [
            ('body', "商稻第一段"),
            ('heading', "春苑标题"),
            ('body', "正常文字"),
        ]
        result = corrector.correct_paragraphs(paragraphs)
        assert result[0][1] == "商務第一段"
        assert result[1][1] == "春秋标题"
        assert result[2][1] == "正常文字"

    def test_load_dictionary_from_file(self):
        """从 JSON 文件加载字典"""
        corrector = Corrector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({"错误词": "正确词", "同义词": "同义词"}, f)
            path = f.name
        try:
            count = corrector.load_dictionary(path)
            assert count == 1  # "同义词"→"同义词" 被过滤
            assert corrector.dictionary_size == 1
        finally:
            os.unlink(path)

    def test_save_and_reload(self):
        """保存并重新加载字典"""
        corrector1 = Corrector()
        corrector1.learn("错别字", "正确字")
        corrector1.learn("测试错", "测试对")

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        try:
            corrector1.save_dictionary(path)
            corrector2 = Corrector()
            count = corrector2.load_dictionary(path)
            assert count == 2
            text, _ = corrector2.correct("错别字和测试错")
            assert text == "正确字和测试对"
        finally:
            os.unlink(path)

    def test_learn_new_correction(self):
        """学习新修正"""
        corrector = Corrector()
        corrector.learn("错词", "对词")
        text, count = corrector.correct("这是错词")
        assert text == "这是对词"
        assert count == 1

    def test_learn_invalid(self):
        """学习无效条目"""
        corrector = Corrector()
        corrector.learn("", "空")
        corrector.learn("同", "同")
        assert corrector.dictionary_size == 0
