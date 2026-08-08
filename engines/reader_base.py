# -*- coding: utf-8 -*-
"""格式读取器基类"""
from abc import ABC, abstractmethod
from engines.document import ParsedDocument


class BaseReader(ABC):
    """格式读取器抽象基类"""

    @abstractmethod
    def read(self, file_path: str) -> ParsedDocument:
        """读取文件，返回统一文档格式"""
        ...
