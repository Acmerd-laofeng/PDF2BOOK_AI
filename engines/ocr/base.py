# -*- coding: utf-8 -*-
"""OCR 引擎抽象接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OCRBlock:
    """OCR 识别块"""
    text: str
    bbox: list       # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    confidence: float = 0.0

    @property
    def x_left(self) -> float:
        return min(p[0] for p in self.bbox)

    @property
    def x_right(self) -> float:
        return max(p[0] for p in self.bbox)

    @property
    def x_center(self) -> float:
        return (self.x_left + self.x_right) / 2

    @property
    def y_top(self) -> float:
        return min(p[1] for p in self.bbox)

    @property
    def y_bot(self) -> float:
        return max(p[1] for p in self.bbox)

    @property
    def y_center(self) -> float:
        return (self.y_top + self.y_bot) / 2

    @property
    def height(self) -> float:
        return self.y_bot - self.y_top

    @property
    def width(self) -> float:
        return self.x_right - self.x_left


class OCREngine(ABC):
    """OCR 引擎抽象接口"""

    @abstractmethod
    def recognize(self, image: bytes) -> List[OCRBlock]:
        """识别图片中的文字

        Args:
            image: 图片字节数据（PNG/JPEG）

        Returns:
            OCRBlock 列表
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        ...
