# -*- coding: utf-8 -*-
"""EPUB 导出器 — 将 ParsedDocument 导出为 EPUB

复用现有 EPUBBuilder 的主题 CSS，但接受 ParsedDocument 输入。
"""
import os
from datetime import datetime
from ebooklib import epub

from engines.exporter_base import BaseExporter
from engines.document import ParsedDocument, Chapter
from engines.export.epub import EPUBBuilder


class EPUBExporter(BaseExporter):
    """EPUB 导出器"""

    def export(self, doc: ParsedDocument, output_path: str, options: dict = None) -> str:
        options = options or {}
        theme = options.get("theme", "classic")

        # 复用 EPUBBuilder 的主题 CSS
        builder = EPUBBuilder()

        book = epub.EpubBook()

        # 元数据
        book.set_identifier(f"pdf2book-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        book.set_title(doc.title or "Untitled")
        book.set_language("zh-CN")
        if doc.author and doc.author != "Unknown":
            book.add_author(doc.author)

        # CSS
        css_content = builder.THEMES.get(theme, builder.THEMES["classic"])
        css_item = epub.EpubItem(
            uid="style",
            file_name="style/default.css",
            media_type="text/css",
            content=css_content.encode("utf-8"),
        )
        book.add_item(css_item)

        # 目录页
        toc_entries = []
        chapters_xhtml = []

        for i, chapter in enumerate(doc.chapters):
            filename = f"chapter_{i + 1:04d}.xhtml"
            title = chapter.title or f"第 {i + 1} 章"

            # 构建 HTML 内容
            html_parts = [
                '<?xml version="1.0" encoding="utf-8"?>',
                '<!DOCTYPE html>',
                '<html xmlns="http://www.w3.org/1999/xhtml">',
                '<head>',
                f'<title>{self._escape(title)}</title>',
                '<link rel="stylesheet" type="text/css" href="style/default.css"/>',
                '</head>',
                '<body>',
                f'<h1>{self._escape(title)}</h1>',
            ]

            for para in chapter.paragraphs:
                if para.strip():
                    html_parts.append(f'<p>{self._escape(para)}</p>')

            html_parts.extend(['</body>', '</html>'])

            content = "\n".join(html_parts)
            chapter_item = epub.EpubHtml(
                title=title,
                file_name=filename,
                content=content.encode("utf-8"),
            )
            chapter_item.add_item(css_item)
            book.add_item(chapter_item)
            chapters_xhtml.append(chapter_item)
            toc_entries.append(chapter_item)

        # 目录
        book.toc = toc_entries

        # 添加 NCX / Nav
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # spine
        book.spine = ["nav"] + chapters_xhtml

        # 写入文件
        epub.write_epub(output_path, book, {})
        return output_path

    @staticmethod
    def _escape(text: str) -> str:
        """HTML 转义"""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text
