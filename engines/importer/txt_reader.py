# -*- coding: utf-8 -*-
"""TXT 读取器 — 解析纯文本为 ParsedDocument"""
import os
import re
from typing import List

from engines.reader_base import BaseReader
from engines.document import ParsedDocument, Chapter
from app.format_constants import TXT_CHAPTER_PATTERNS


class TXTReader(BaseReader):
    """纯文本解析器"""

    def read(self, file_path: str) -> ParsedDocument:
        doc = ParsedDocument(
            title=os.path.splitext(os.path.basename(file_path))[0],
            source_format="txt",
            source_path=file_path,
        )

        # 尝试多种编码
        text = None
        for encoding in ["utf-8", "gbk", "gb2312", "big5", "utf-16"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    text = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if text is None:
            raise ValueError("无法识别文件编码，尝试了 UTF-8/GBK/GB2312/Big5/UTF-16")

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 按章节模式分章
        compiled = [re.compile(p) for p in TXT_CHAPTER_PATTERNS]

        current_chapter = Chapter(title="前言" if lines else "")
        doc.chapters.append(current_chapter)

        for line in lines:
            is_heading = any(p.match(line) for p in compiled)
            if is_heading and len(line) < 50:
                current_chapter = Chapter(title=line)
                doc.chapters.append(current_chapter)
            else:
                current_chapter.paragraphs.append(line)

        # 清理空的首章
        if doc.chapters and not doc.chapters[0].title and not doc.chapters[0].paragraphs:
            doc.chapters.pop(0)

        doc.compute_stats()
        return doc
