# -*- coding: utf-8 -*-
"""RapidOCR 引擎实现"""
from typing import List

from engines.ocr.base import OCREngine, OCRBlock


class RapidOCREngine(OCREngine):
    """RapidOCR 引擎

    纯 pip 安装，自带 ONNX 模型，打包友好。
    """

    def __init__(self):
        self._engine = None

    def _ensure_engine(self):
        """延迟初始化引擎"""
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR
            self._engine = RapidOCR()

    def recognize(self, image: bytes) -> List[OCRBlock]:
        """识别图片中的文字"""
        self._ensure_engine()

        result = self._engine(image)
        if not result or not result[0]:
            return []

        blocks = []
        for item in result[0]:
            if len(item) < 2 or not item[1]:
                continue
            bbox = item[0]
            text = item[1].strip()
            conf = item[2] if len(item) > 2 else 0.0

            if not text:
                continue

            blocks.append(OCRBlock(
                text=text,
                bbox=bbox,
                confidence=float(conf),
            ))

        return blocks

    def is_available(self) -> bool:
        """检查是否可用"""
        try:
            import rapidocr_onnxruntime
            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return "RapidOCR"
