# -*- coding: utf-8 -*-
"""导出器基类"""
from abc import ABC, abstractmethod
from engines.document import ParsedDocument


class BaseExporter(ABC):
    """格式导出器抽象基类"""

    @abstractmethod
    def export(self, doc: ParsedDocument, output_path: str, options: dict = None) -> str:
        """导出文档到目标格式

        Args:
            doc: 统一文档格式
            output_path: 输出文件路径
            options: 导出选项

        Returns:
            实际输出文件路径
        """
        ...
