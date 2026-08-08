# -*- coding: utf-8 -*-
"""EPUB 导出器 — 将 ParsedDocument 导出为 EPUB

v4.0.5 改进：
- 新增封面页（书名 + 作者）
- HTML 转义更完整（引号也转义）
- 空/单章文档自动补标题
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

        builder = EPUBBuilder()
        book = epub.EpubBook()

        # 元数据
        book.set_identifier(f"pdf2book-{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
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

        # === 封面页 ===
        title = doc.title or "Untitled"
        author = doc.author if doc.author and doc.author != "Unknown" else ""
        cover_html = self._build_cover_html(title, author)
        cover_item = epub.EpubHtml(
            title="封面",
            file_name="cover.xhtml",
            content=cover_html.encode("utf-8"),
        )
        cover_item.add_item(css_item)
        book.add_item(cover_item)

        # === 章节页 ===
        toc_entries = []
        chapters_xhtml = []

        # 如果没有章节，创建一个默认章节
        if not doc.chapters:
            doc.add_chapter(title="正文", paragraphs=[])

        for i, chapter in enumerate(doc.chapters):
            filename = f"chapter_{i + 1:04d}.xhtml"
            ch_title = chapter.title or f"第 {i + 1} 章"

            html_parts = [
                '<?xml version="1.0" encoding="utf-8"?>',
                '<!DOCTYPE html>',
                '<html xmlns="http://www.w3.org/1999/xhtml">',
                '<head>',
                f'<title>{self._escape(ch_title)}</title>',
                '<link rel="stylesheet" type="text/css" href="style/default.css"/>',
                '</head>',
                '<body>',
                f'<h1>{self._escape(ch_title)}</h1>',
            ]

            for para in chapter.paragraphs:
                if para.strip():
                    html_parts.append(f'<p>{self._escape(para)}</p>')

            html_parts.extend(['</body>', '</html>'])
            content = "\n".join(html_parts)

            chapter_item = epub.EpubHtml(
                title=ch_title,
                file_name=filename,
                content=content.encode("utf-8"),
            )
            chapter_item.add_item(css_item)
            book.add_item(chapter_item)
            chapters_xhtml.append(chapter_item)
            toc_entries.append(chapter_item)

        # 目录
        book.toc = toc_entries

        # NCX / Nav
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # spine: 封面 → 目录 → 正文章节
        book.spine = [cover_item, "nav"] + chapters_xhtml

        epub.write_epub(output_path, book, {})
        return output_path

    def _build_cover_html(self, title: str, author: str) -> str:
        """构建封面页 HTML"""
        parts = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<head>',
            f'<title>{self._escape(title)}</title>',
            '<link rel="stylesheet" type="text/css" href="style/default.css"/>',
            '</head>',
            '<body>',
            '<div class="cover" style="text-align:center; padding-top:30%;">',
            f'<h1 style="font-size:2em;">{self._escape(title)}</h1>',
        ]
        if author:
            parts.append(f'<p style="color:#666; font-size:1.1em;">{self._escape(author)}</p>')
        parts.extend([
            '</div>',
            '</body>',
            '</html>',
        ])
        return "\n".join(parts)

    @staticmethod
    def _escape(text: str) -> str:
        """完整 HTML 转义"""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#39;")
        return text
