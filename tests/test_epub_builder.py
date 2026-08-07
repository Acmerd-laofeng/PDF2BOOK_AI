# -*- coding: utf-8 -*-
"""EPUB 生成器单元测试"""
import os
import tempfile
import pytest
from engines.export.epub import EPUBBuilder


class TestEPUBBuilder:

    @pytest.fixture
    def builder(self):
        return EPUBBuilder()

    @pytest.fixture
    def sample_paragraphs(self):
        return [
            ('heading', "第一章 开始"),
            ('body', "这是第一段内容。"),
            ('body', "这是第二段内容。"),
            ('heading', "第二章 继续"),
            ('body', "第三章的内容。"),
        ]

    def test_build_epub(self, builder, sample_paragraphs):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "test.epub")
            stats = builder.build(
                paragraphs=sample_paragraphs,
                title="测试书籍",
                author="测试作者",
                output_path=output,
                theme="classic",
            )
            assert os.path.exists(output)
            assert os.path.getsize(output) > 0
            # 验证返回的统计信息
            assert stats["chapter_count"] == 2
            assert stats["total_paragraphs"] == 5
            assert stats["heading_count"] == 2
            assert stats["body_count"] == 3
            assert stats["total_chars"] > 0
            assert stats["output_path"] == output
            assert stats["file_size"] > 0
            assert len(stats["chapter_titles"]) == 2

    def test_build_no_chapters(self, builder):
        """无标题分隔的文本"""
        paragraphs = [
            ('body', "第一段。"),
            ('body', "第二段。"),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "no_chap.epub")
            stats = builder.build(
                paragraphs=paragraphs,
                title="无章节书",
                author="匿名",
                output_path=output,
            )
            assert os.path.exists(output)
            assert stats["chapter_count"] >= 1
            assert stats["total_paragraphs"] >= 2

    def test_build_no_chapters_with_size_split(self, builder):
        """无标题、段落数多时按大小分章"""
        paragraphs = [('body', f"第{i}段内容。") for i in range(120)]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "big.epub")
            stats = builder.build(
                paragraphs=paragraphs,
                title="大书",
                author="匿名",
                output_path=output,
            )
            assert os.path.exists(output)
            assert stats["chapter_count"] >= 2  # 应该被分章

    def test_themes_exist(self, builder):
        """所有主题 CSS 都存在"""
        for theme in ["classic", "kindle", "modern", "eye_care"]:
            assert theme in EPUBBuilder.THEMES
            assert "body" in EPUBBuilder.THEMES[theme]

    def test_html_escape(self, builder):
        """HTML 转义"""
        assert builder._escape_html("<script>") == "&lt;script&gt;"
        assert builder._escape_html("a & b") == "a &amp; b"
        assert builder._escape_html('"quote"') == "&quot;quote&quot;"

    def test_external_theme_loading(self, builder):
        """从外部文件加载主题 CSS"""
        with tempfile.TemporaryDirectory() as tmpdir:
            css_path = os.path.join(tmpdir, "test.css")
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write("body { custom: true; }")
            css = builder._load_theme_css("test", tmpdir)
            assert "custom: true" in css

    def test_fallback_theme(self, builder):
        """不存在的主题回退到 classic"""
        css = builder._load_theme_css("nonexistent", None)
        assert "body" in css  # classic 主题内容
