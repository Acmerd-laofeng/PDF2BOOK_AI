# -*- coding: utf-8 -*-
"""MOBI 导出器 — 将 ParsedDocument 导出为 MOBI

策略：先生成 EPUB，再用 ebooklib 或 calibre 的 ebook-convert 转为 MOBI。
若 calibre 未安装，输出 .epub 并提示用户手动转换。
"""
import os
import subprocess
import tempfile

from engines.exporter_base import BaseExporter
from engines.document import ParsedDocument
from engines.export.epub_exporter import EPUBExporter


class MOBIExporter(BaseExporter):
    """MOBI 导出器"""

    def export(self, doc: ParsedDocument, output_path: str, options: dict = None) -> str:
        options = options or {}

        # 先生成临时 EPUB
        temp_epub = output_path.rsplit(".", 1)[0] + "_temp.epub"
        epub_exporter = EPUBExporter()
        epub_exporter.export(doc, temp_epub, options)

        # 尝试用 calibre ebook-convert 转 MOBI
        try:
            result = subprocess.run(
                ["ebook-convert", temp_epub, output_path],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                os.unlink(temp_epub)
                return output_path
            else:
                # ebook-convert 失败，保留 EPUB 作为备选
                if os.path.exists(output_path):
                    os.unlink(output_path)
                os.rename(temp_epub, output_path.rsplit(".", 1)[0] + ".epub")
                raise RuntimeError(
                    "Calibre ebook-convert 转换 MOBI 失败，已输出 EPUB 作为替代。\n"
                    "如需 MOBI，请安装 Calibre: https://calibre-ebook.com/download"
                )

        except FileNotFoundError:
            # calibre 未安装
            os.rename(temp_epub, output_path.rsplit(".", 1)[0] + ".epub")
            raise RuntimeError(
                "未找到 Calibre ebook-convert，已输出 EPUB 作为替代。\n"
                "如需 MOBI，请安装 Calibre: https://calibre-ebook.com/download"
            )
