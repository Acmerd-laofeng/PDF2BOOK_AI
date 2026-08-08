# -*- coding: utf-8 -*-
"""读取器注册表 — 根据格式自动选择读取器"""
import os

from engines.reader_base import BaseReader
from engines.document import ParsedDocument
from engines.importer.pdf_reader import PDFReader
from engines.importer.epub_reader import EPUBReader
from engines.importer.txt_reader import TXTReader
from engines.importer.mobi_reader import MOBIReader


# 格式 → 读取器映射
_READERS = {
    "pdf": PDFReader,
    "epub": EPUBReader,
    "txt": TXTReader,
    "mobi": MOBIReader,
}


def get_reader(file_path: str) -> BaseReader:
    """根据文件扩展名获取读取器"""
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    reader_cls = _READERS.get(ext)
    if not reader_cls:
        raise ValueError(f"不支持的文件格式: .{ext}，支持: {', '.join(_READERS.keys())}")
    return reader_cls()


def read_document(file_path: str) -> ParsedDocument:
    """读取文档，返回统一中间格式"""
    reader = get_reader(file_path)
    return reader.read(file_path)


def get_supported_formats() -> list:
    """获取支持的读取格式"""
    return list(_READERS.keys())
