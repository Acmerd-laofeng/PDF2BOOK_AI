# -*- coding: utf-8 -*-
"""EPUB 读取器 — 解析 EPUB 为 ParsedDocument"""
import os
import re
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

from engines.reader_base import BaseReader
from engines.document import ParsedDocument, Chapter


class EPUBReader(BaseReader):
    """EPUB 文件解析器"""

    def read(self, file_path: str) -> ParsedDocument:
        doc = ParsedDocument(
            title=os.path.splitext(os.path.basename(file_path))[0],
            source_format="epub",
            source_path=file_path,
        )

        book = epub.read_epub(file_path)

        # 元数据
        if book.get_metadata("DC", "title"):
            doc.title = book.get_metadata("DC", "title")[0][0]
        if book.get_metadata("DC", "creator"):
            doc.author = book.get_metadata("DC", "creator")[0][0]

        # 遍历文档项
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            content = item.get_content()
            soup = BeautifulSoup(content, "html.parser")

            # 从文件名猜测章节标题
            item_name = item.get_name() or ""
            chapter_title = self._extract_title_from_html(soup) or os.path.basename(item_name)

            paragraphs = []
            for tag in soup.find_all(["p", "div"]):
                text = tag.get_text(strip=True)
                if text:
                    paragraphs.append(text)

            if paragraphs:
                chapter = Chapter(
                    title=chapter_title,
                    paragraphs=paragraphs,
                )
                doc.chapters.append(chapter)

        # 如果没有分出章节，把所有文本放一个章节
        if not doc.chapters:
            all_text = []
            for item in book.get_items_of_type(ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text = soup.get_text(separator="\n")
                for line in text.split("\n"):
                    line = line.strip()
                    if line:
                        all_text.append(line)
            if all_text:
                doc.add_chapter(title="正文", paragraphs=all_text)

        doc.compute_stats()
        return doc

    def _extract_title_from_html(self, soup: BeautifulSoup) -> str:
        """从 HTML 中提取标题"""
        for tag_name in ["h1", "h2", "h3"]:
            tag = soup.find(tag_name)
            if tag:
                return tag.get_text(strip=True)
        return ""
