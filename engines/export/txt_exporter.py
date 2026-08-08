# -*- coding: utf-8 -*-
"""TXT 导出器 — 将 ParsedDocument 导出为纯文本

v4.0.5 改进：
- 段落间加空行（可读性）
- 章节标题前后加空行
- 编码 BOM 选项（UTF-8 BOM 方便 Windows 记事本）
"""
import os

from engines.exporter_base import BaseExporter
from engines.document import ParsedDocument


class TXTExporter(BaseExporter):
    """纯文本导出器"""

    def export(self, doc: ParsedDocument, output_path: str, options: dict = None) -> str:
        options = options or {}
        encoding = options.get("encoding", "utf-8")
        chapter_sep = options.get("chapter_separator", "\n\n")
        add_bom = options.get("add_bom", False)

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
                lines.append("")  # 标题前空行
                lines.append(chapter.title)
                lines.append("-" * 30)
                lines.append("")  # 标题后空行

            for para in chapter.paragraphs:
                lines.append(para)
                lines.append("")  # 段落间空行

            if i < len(doc.chapters) - 1:
                lines.append(chapter_sep.strip())

        # 写入文件
        content = "\n".join(lines)
        if encoding == "utf-8" and add_bom:
            with open(output_path, "w", encoding="utf-8-sig") as f:
                f.write(content)
        else:
            with open(output_path, "w", encoding=encoding) as f:
                f.write(content)

        return output_path
