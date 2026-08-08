# -*- coding: utf-8 -*-
"""PDF 读取器 — 提取文本和结构为 ParsedDocument

复用现有 PyMuPDF 引擎，不走 OCR。
适用于文本型 PDF（扫描版 PDF 需走 OCR Pipeline）。
"""
import os
import re
import fitz  # PyMuPDF
from typing import List

from engines.reader_base import BaseReader
from engines.document import ParsedDocument, Chapter
from app.constants import CHAPTER_PATTERNS


class PDFReader(BaseReader):
    """PDF 文本提取器"""

    def read(self, file_path: str) -> ParsedDocument:
        doc = ParsedDocument(
            title=os.path.splitext(os.path.basename(file_path))[0],
            source_format="pdf",
            source_path=file_path,
        )

        pdf = fitz.open(file_path)

        # 尝试从元数据获取标题和作者
        meta = pdf.metadata
        if meta:
            if meta.get("title"):
                doc.title = meta["title"]
            if meta.get("author"):
                doc.author = meta["author"]

        all_text_lines: List[str] = []
        for page in pdf:
            text = page.get_text("text")
            if text:
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                all_text_lines.extend(lines)

        pdf.close()

        # 按章节模式分章
        doc = self._split_chapters(doc, all_text_lines)
        doc.compute_stats()
        return doc

    def _split_chapters(self, doc: ParsedDocument, lines: List[str]) -> ParsedDocument:
        """按章节正则分章，并合并连续行为段落"""
        compiled = [re.compile(p) for p in CHAPTER_PATTERNS]

        current_chapter = Chapter(title="前言" if lines else "")
        doc.chapters.append(current_chapter)

        for line in lines:
            is_heading = any(p.match(line) for p in compiled)
            if is_heading and len(line) < 50:
                # 新章节
                current_chapter = Chapter(title=line)
                doc.chapters.append(current_chapter)
            else:
                # 合并连续行：如果当前段落不为空且本行不是新段落开头，
                # 则追加到当前段落
                if current_chapter.paragraphs:
                    last_para = current_chapter.paragraphs[-1]
                    # 简单规则：如果上一行以句末标点结尾，开始新段落
                    if last_para and last_para[-1] in '。！？…」』）)]}】':
                        current_chapter.paragraphs.append(line)
                    else:
                        # 否则合并到上一段落
                        current_chapter.paragraphs[-1] = last_para + line
                else:
                    current_chapter.paragraphs.append(line)

        # 如果第一个章节没有内容也没有标题，删除
        if doc.chapters and not doc.chapters[0].title and not doc.chapters[0].paragraphs:
            doc.chapters.pop(0)

        return doc
