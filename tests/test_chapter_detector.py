# -*- coding: utf-8 -*-
"""章节检测器单元测试"""
import pytest
from engines.layout.chapter_detector import ChapterDetector


class TestChapterDetector:

    @pytest.fixture
    def detector(self):
        return ChapterDetector()

    def test_chinese_chapter(self, detector):
        assert detector._is_chapter_title("第一章 风起云涌")
        assert detector._is_chapter_title("第二回 桃花岛")
        assert detector._is_chapter_title("第三节 开始")

    def test_english_chapter(self, detector):
        assert detector._is_chapter_title("Chapter 1")
        assert detector._is_chapter_title("Chapter 99")

    def test_special_titles(self, detector):
        assert detector._is_chapter_title("序")
        assert detector._is_chapter_title("前言")
        assert detector._is_chapter_title("后记")
        assert detector._is_chapter_title("目录")
        assert detector._is_chapter_title("附录A")

    def test_not_chapter(self, detector):
        assert not detector._is_chapter_title("这是一段正文")
        assert not detector._is_chapter_title("")
        assert not detector._is_chapter_title("a" * 60)

    def test_detect_and_mark(self, detector):
        paragraphs = [
            ('body', "第一章 开始"),
            ('body', "正文内容"),
            ('body', "第二章 继续"),
            ('body', "更多正文"),
        ]
        result = detector.detect_and_mark(paragraphs)
        assert result[0][0] == 'heading'
        assert result[1][0] == 'body'
        assert result[2][0] == 'heading'
        assert result[3][0] == 'body'

    def test_extract_chapters(self, detector):
        paragraphs = [
            ('heading', "第一章"),
            ('body', "内容1"),
            ('heading', "第二章"),
            ('body', "内容2"),
        ]
        chapters = detector.extract_chapters(paragraphs)
        assert len(chapters) == 2
        assert chapters[0]['title'] == "第一章"
        assert chapters[1]['title'] == "第二章"
