# -*- coding: utf-8 -*-
"""bbox 坐标解析器 - 从 v2 迁移

从 OCR 原始结果中提取标准化 Block 列表。
"""
from typing import List

from engines.ocr.base import OCRBlock


class BBoxParser:
    """bbox 坐标解析器

    输入：OCR 原始结果
    输出：按 Y 坐标排序的 OCRBlock 列表
    """

    def parse(self, raw_result) -> List[OCRBlock]:
        """解析 OCR 原始结果

        Args:
            raw_result: RapidOCR 返回的 (results, elapsed) 元组

        Returns:
            OCRBlock 列表
        """
        if not raw_result or not raw_result[0]:
            return []

        blocks = []
        for item in raw_result[0]:
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

        # 按 Y 坐标排序
        blocks.sort(key=lambda b: b.y_top)
        return blocks

    def parse_page_size(self, blocks: List[OCRBlock]) -> tuple:
        """从 blocks 推断页面尺寸

        Returns:
            (page_width, page_height)
        """
        if not blocks:
            return (0, 0)
        page_w = max(b.x_right for b in blocks)
        page_h = max(b.y_bot for b in blocks)
        return (page_w, page_h)
