# -*- coding: utf-8 -*-
"""MOBI 读取器 — 解析 MOBI 为 ParsedDocument

依赖 ebooklib（支持 MOBI 读取）。
若 ebooklib 无法直接读 MOBI，回退到 kindleunpack 或标记不支持。
"""
import os
import re
from typing import List

from engines.reader_base import BaseReader
from engines.document import ParsedDocument, Chapter


class MOBIReader(BaseReader):
    """MOBI 文件解析器"""

    def read(self, file_path: str) -> ParsedDocument:
        doc = ParsedDocument(
            title=os.path.splitext(os.path.basename(file_path))[0],
            source_format="mobi",
            source_path=file_path,
        )

        # ebooklib 对 MOBI 支持有限，尝试读取
        try:
            from ebooklib import epub
            book = epub.read_epub(file_path)
            # ebooklib 有时能把 MOBI 当 EPUB 读

            if book.get_metadata("DC", "title"):
                doc.title = book.get_metadata("DC", "title")[0][0]
            if book.get_metadata("DC", "creator"):
                doc.author = book.get_metadata("DC", "creator")[0][0]

            from ebooklib import ITEM_DOCUMENT
            from bs4 import BeautifulSoup

            for item in book.get_items_of_type(ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_content(), "html.parser")
                chapter_title = ""
                for tag_name in ["h1", "h2", "h3"]:
                    tag = soup.find(tag_name)
                    if tag:
                        chapter_title = tag.get_text(strip=True)
                        break

                paragraphs = []
                for tag in soup.find_all(["p", "div"]):
                    text = tag.get_text(strip=True)
                    if text:
                        paragraphs.append(text)

                if paragraphs:
                    doc.add_chapter(
                        title=chapter_title or f"章节 {len(doc.chapters) + 1}",
                        paragraphs=paragraphs,
                    )

        except Exception:
            # MOBI 直接解析失败，尝试用 mobi 库
            try:
                import mobi  # pip install mobi
                tempdir, filepath = mobi.extract(file_path)
                # 提取后通常是 HTML/EPUB
                if filepath.endswith(".html"):
                    from bs4 import BeautifulSoup
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")

                    all_text = []
                    for tag in soup.find_all(["p", "div", "br"]):
                        text = tag.get_text(strip=True)
                        if text:
                            all_text.append(text)

                    # 简单分章
                    chapter_patterns = [
                        r"^第[一二三四五六七八九十百千零〇\d]+[章回节].*",
                        r"^Chapter\s+\d+.*",
                    ]
                    compiled = [re.compile(p) for p in chapter_patterns]
                    current = Chapter(title="正文")
                    doc.chapters.append(current)
                    for line in all_text:
                        if any(p.match(line) for p in compiled) and len(line) < 50:
                            current = Chapter(title=line)
                            doc.chapters.append(current)
                        else:
                            current.paragraphs.append(line)

                import shutil
                shutil.rmtree(tempdir, ignore_errors=True)

            except ImportError:
                raise ValueError(
                    "MOBI 解析需要安装 mobi 库：pip install mobi\n"
                    "或使用 ebooklib（对部分 MOBI 文件兼容）"
                )

        if not doc.chapters:
            doc.add_chapter(title="正文", paragraphs=[])

        doc.compute_stats()
        return doc
