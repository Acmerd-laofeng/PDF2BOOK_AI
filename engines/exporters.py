# -*- coding: utf-8 -*-
"""导出器注册表 — 根据目标格式选择导出器

MOBI 不作为导出目标（Kindle 2022 起停止 MOBI 支持，全面转向 EPUB）。
"""
from engines.exporter_base import BaseExporter
from engines.document import ParsedDocument
from engines.export.txt_exporter import TXTExporter
from engines.export.pdf_exporter import PDFExporter
from engines.export.epub_exporter import EPUBExporter


# 格式 → 导出器映射（不含 mobi）
_EXPORTERS = {
    "txt": TXTExporter,
    "pdf": PDFExporter,
    "epub": EPUBExporter,
}


def get_exporter(target_format: str) -> BaseExporter:
    """获取导出器"""
    exporter_cls = _EXPORTERS.get(target_format.lower())
    if not exporter_cls:
        raise ValueError(
            f"不支持的导出格式: {target_format}，支持: {', '.join(_EXPORTERS.keys())}"
        )
    return exporter_cls()


def export_document(doc: ParsedDocument, output_path: str,
                    target_format: str = None,
                    options: dict = None) -> str:
    """导出文档到目标格式

    Args:
        doc: 统一文档格式
        output_path: 输出路径
        target_format: 目标格式（如未指定，从 output_path 扩展名推断）
        options: 导出选项

    Returns:
        实际输出文件路径
    """
    if not target_format:
        import os
        target_format = os.path.splitext(output_path)[1].lower().lstrip(".")

    exporter = get_exporter(target_format)
    return exporter.export(doc, output_path, options)


def get_supported_formats() -> list:
    """获取支持的导出格式"""
    return list(_EXPORTERS.keys())
