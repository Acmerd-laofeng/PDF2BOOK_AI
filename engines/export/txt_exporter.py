# -*- coding: utf-8 -*-
"""TXT 导出器 — 将 ParsedDocument 导出为纯文本"""
import os

from engines.exporter_base import BaseExporter
from engines.document import ParsedDocument


class TXTExporter(BaseExporter):
    """纯文本导出器"""

    def export(self, doc: ParsedDocument, output_path: str, options: dict = None) -> str:
        options = options or {}
        encoding = options.get("encoding", "utf-8")
        chapter_sep = options.get("chapter_separator", "\n\n")

        lines = []

        # 书名
        if doc.title:
            lines.append(doc.title)
            lines.append("=" * 40)
            lines.append("")

        # 作者
        if doc.author and doc.author != "Unknown":
            lines.append(f"作者: {doc.author}")
            lines.append("")

        # 章节
        for i, chapter in enumerate(doc.chapters):
            if chapter.title:
                lines.append(chapter.title)
                lines.append("-" * 30)

            for para in chapter.paragraphs:
                lines.append(para)

            if i < len(doc.chapters) - 1:
                lines.append(chapter_sep)

        # 写入文件
        with open(output_path, "w", encoding=encoding) as f:
            f.write("\n".join(lines))

        return output_path
