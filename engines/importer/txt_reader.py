# -*- coding: utf-8 -*-
"""TXT 读取器 — 解析纯文本为 ParsedDocument

v4.0.5 改进：
- 段落合并：按空行+缩进分段，而非逐行成段
- 章节分章：正则匹配 + 上下文验证
- 编码检测：UTF-8/GBK/GB2312/Big5/UTF-16 + BOM 检测
"""
import os
import re
from typing import List

from engines.reader_base import BaseReader
from engines.document import ParsedDocument, Chapter
from app.format_constants import TXT_CHAPTER_PATTERNS

# 句末标点
_SENTENCE_END = '。！？…」』）)]}】!?;；'


class TXTReader(BaseReader):
    """纯文本解析器"""

    def read(self, file_path: str) -> ParsedDocument:
        doc = ParsedDocument(
            title=os.path.splitext(os.path.basename(file_path))[0],
            source_format="txt",
            source_path=file_path,
        )

        text = self._read_file(file_path)
        if text is None:
            raise ValueError("无法识别文件编码，尝试了 UTF-8/GBK/GB2312/Big5/UTF-16")

        # 按段落分段（空行分段 + 连续行合并 + 标题独立）
        compiled_patterns = TXT_CHAPTER_PATTERNS
        paragraphs = self._split_paragraphs(text, compiled_patterns)

        # 按章节模式分章
        compiled = [re.compile(p) for p in TXT_CHAPTER_PATTERNS]

        current_chapter = Chapter(title="前言" if paragraphs else "")
        doc.chapters.append(current_chapter)

        for para in paragraphs:
            is_heading = any(p.match(para) for p in compiled)
            if is_heading and len(para) < 50:
                current_chapter = Chapter(title=para)
                doc.chapters.append(current_chapter)
            else:
                current_chapter.paragraphs.append(para)

        # 清理空的首章
        if doc.chapters and not doc.chapters[0].title and not doc.chapters[0].paragraphs:
            doc.chapters.pop(0)

        doc.compute_stats()
        return doc

    def _read_file(self, file_path: str) -> str:
        """多编码读取，BOM 优先"""
        # BOM 检测
        with open(file_path, "rb") as f:
            raw = f.read(4)

        bom_map = {
            b'\xef\xbb\xbf': 'utf-8-sig',
            b'\xff\xfe\x00\x00': 'utf-32-le',
            b'\x00\x00\xfe\xff': 'utf-32-be',
            b'\xff\xfe': 'utf-16-le',
            b'\xfe\xff': 'utf-16-be',
        }
        for bom, enc in bom_map.items():
            if raw.startswith(bom):
                try:
                    with open(file_path, "r", encoding=enc) as f:
                        return f.read()
                except (UnicodeDecodeError, UnicodeError):
                    break

        # 无 BOM，逐个尝试
        for encoding in ["utf-8", "gbk", "gb2312", "big5", "utf-16"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue

        return None

    def _split_paragraphs(self, text: str, chapter_patterns: list = None) -> List[str]:
        """将文本拆分为段落

        规则：
        1. 空行分隔 → 独立段落
        2. 章节标题行 → 独立段落（不被合并）
        3. 连续非空行 → 合并为一个段落（句末标点结尾断段）
        """
        compiled = [re.compile(p) for p in (chapter_patterns or [])]

        # 按空行分段
        raw_blocks = re.split(r'\n\s*\n', text)

        paragraphs = []
        for block in raw_blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if not lines:
                continue

            if len(lines) == 1:
                paragraphs.append(lines[0])
            else:
                # 多行合并：逐行判断是否需要断段
                current = lines[0]
                # 检查首行是否是标题
                is_first_heading = any(p.match(current) for p in compiled) if compiled else False
                if is_first_heading and len(current) < 50:
                    paragraphs.append(current)
                    current = ""

                for i in range(1, len(lines)):
                    line = lines[i]
                    # 章节标题行 → 独立段落
                    is_heading = any(p.match(line) for p in compiled) if compiled else False
                    if is_heading and len(line) < 50:
                        if current:
                            paragraphs.append(current)
                        paragraphs.append(line)
                        current = ""
                        continue
                    # 上一行以句末标点结尾 → 新段落
                    if current and current[-1] in _SENTENCE_END:
                        paragraphs.append(current)
                        current = line
                    else:
                        current += line
                if current:
                    paragraphs.append(current)

        return paragraphs
