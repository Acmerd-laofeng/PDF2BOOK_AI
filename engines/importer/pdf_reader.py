# -*- coding: utf-8 -*-
"""PDF 读取器 — 提取文本和结构为 ParsedDocument

v4.0.5 改进：
- 段落合并：不仅看句末标点，还考虑 PyMuPDF 的 block 结构
- 页眉页脚过滤：重复出现的顶部/底部行自动过滤
- 章节检测：复用 CHAPTER_PATTERNS
"""
import os
import re
import fitz  # PyMuPDF
from typing import List
from collections import Counter

from engines.reader_base import BaseReader
from engines.document import ParsedDocument, Chapter
from app.constants import CHAPTER_PATTERNS

# 句末标点
_SENTENCE_END = '。！？…」』）)]}】!?;；'


class PDFReader(BaseReader):
    """PDF 文本提取器"""

    def read(self, file_path: str) -> ParsedDocument:
        doc = ParsedDocument(
            title=os.path.splitext(os.path.basename(file_path))[0],
            source_format="pdf",
            source_path=file_path,
        )

        pdf = fitz.open(file_path)

        # 元数据
        meta = pdf.metadata
        if meta:
            if meta.get("title"):
                doc.title = meta["title"]
            if meta.get("author"):
                doc.author = meta["author"]

        # 提取所有页的行文本，同时收集页眉页脚候选
        all_lines: List[str] = []
        header_footer_candidates = Counter()

        for page in pdf:
            text = page.get_text("text")
            if not text:
                continue
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if not lines:
                continue

            # 收集首尾行作为页眉页脚候选
            if len(lines) >= 3:
                header_footer_candidates[lines[0]] += 1
                header_footer_candidates[lines[-1]] += 1

            all_lines.extend(lines)

        pdf.close()

        # 过滤页眉页脚（出现次数 >= 3 的首尾行视为页眉页脚）
        page_count = len(header_footer_candidates)
        hf_set = {
            line for line, count in header_footer_candidates.items()
            if count >= 3
        }
        if hf_set:
            all_lines = [l for l in all_lines if l not in hf_set]

        # 按章节分章 + 段落合并
        doc = self._split_chapters(doc, all_lines)
        doc.compute_stats()
        return doc

    def _split_chapters(self, doc: ParsedDocument, lines: List[str]) -> ParsedDocument:
        """按章节正则分章，并合并连续行为段落

        段落合并规则：
        1. 上一行以句末标点结尾 → 新段落
        2. 当前行为章节标题 → 新章节
        3. 否则合并到上一行
        """
        compiled = [re.compile(p) for p in CHAPTER_PATTERNS]

        current_chapter = Chapter(title="前言" if lines else "")
        doc.chapters.append(current_chapter)

        for line in lines:
            is_heading = any(p.match(line) for p in compiled)
            if is_heading and len(line) < 50:
                current_chapter = Chapter(title=line)
                doc.chapters.append(current_chapter)
            else:
                if current_chapter.paragraphs:
                    last_para = current_chapter.paragraphs[-1]
                    # 上一行以句末标点结尾 → 新段落
                    if last_para and last_para[-1] in _SENTENCE_END:
                        current_chapter.paragraphs.append(line)
                    else:
                        # 合并到上一段落
                        current_chapter.paragraphs[-1] = last_para + line
                else:
                    current_chapter.paragraphs.append(line)

        # 清理空的首章
        if doc.chapters and not doc.chapters[0].title and not doc.chapters[0].paragraphs:
            doc.chapters.pop(0)

        return doc
