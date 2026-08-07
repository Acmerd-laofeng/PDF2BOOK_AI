# -*- coding: utf-8 -*-
"""表格检测器（预留，v4 实现）"""
from typing import List
from engines.ocr.base import OCRBlock


class TableDetector:
    """表格检测器

    预留接口，未来基于以下特征检测表格：
    - 水平/垂直线条
    - 单元格对齐模式
    - 规则网格布局
    """

    def detect(self, blocks: List[OCRBlock]) -> List[dict]:
        """检测表格区域

        Returns:
            表格信息列表 [{'bbox': [...], 'rows': N, 'cols': M}, ...]
        """
        # TODO: v4 实现
        return []

    def extract_table(self, blocks: List[OCRBlock], table_bbox: list) -> List[List[str]]:
        """提取表格内容

        Returns:
            二维数组 [[cell, cell, ...], [cell, ...], ...]
        """
        # TODO: v4 实现
        return []
