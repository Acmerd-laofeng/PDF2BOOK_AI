# -*- coding: utf-8 -*-
"""统一文档中间格式 — 格式转换的内部数据结构

所有格式的文档在转换前先解析为 ParsedDocument，
然后再导出为目标格式。

这样只需 N 个读取器 + M 个导出器，而非 N×M 个转换器。
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Chapter:
    """章节"""
    title: str = ""
    paragraphs: List[str] = field(default_factory=list)
    images: List[bytes] = field(default_factory=list)  # 图片二进制数据


@dataclass
class ParsedDocument:
    """解析后的统一文档格式"""
    title: str = ""
    author: str = ""
    chapters: List[Chapter] = field(default_factory=list)
    total_chars: int = 0
    source_format: str = ""   # 源格式: pdf/epub/txt/mobi
    source_path: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    def add_chapter(self, title: str = "", paragraphs: List[str] = None) -> Chapter:
        ch = Chapter(title=title, paragraphs=paragraphs or [])
        self.chapters.append(ch)
        return ch

    def compute_stats(self):
        """统计总字数"""
        self.total_chars = sum(
            sum(len(p) for p in ch.paragraphs)
            for ch in self.chapters
        )
        return self.total_chars
