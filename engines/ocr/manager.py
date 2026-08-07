# -*- coding: utf-8 -*-
"""OCR 管理器 - 自动选择引擎"""
from typing import List

from engines.ocr.base import OCREngine, OCRBlock
from engines.ocr.rapidocr_engine import RapidOCREngine


class OCRManager:
    """OCR 引擎管理器

    自动选择可用的 OCR 引擎。
    当前默认 RapidOCR，未来可扩展 PaddleOCR GPU 等。
    """

    def __init__(self):
        self._engine: OCREngine = None
        self._engines: List[OCREngine] = [
            RapidOCREngine(),
        ]

    def _get_engine(self) -> OCREngine:
        """获取可用引擎"""
        if self._engine is not None:
            return self._engine

        for engine in self._engines:
            if engine.is_available():
                self._engine = engine
                return engine

        raise RuntimeError("没有可用的 OCR 引擎，请安装 rapidocr-onnxruntime")

    def run(self, image: bytes) -> List[OCRBlock]:
        """执行 OCR 识别"""
        engine = self._get_engine()
        return engine.recognize(image)

    @property
    def engine_name(self) -> str:
        """当前引擎名称"""
        try:
            return self._get_engine().name
        except RuntimeError:
            return "None"
