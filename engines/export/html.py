# -*- coding: utf-8 -*-
"""HTML 输出（预留，v5 实现）"""
from typing import List, Tuple


class HTMLBuilder:
    """HTML 格式生成器"""

    def build(self, paragraphs: List[Tuple[str, str]],
              title: str, output_path: str,
              theme_css: str = ""):
        """生成 HTML 文件"""
        # TODO: v5 实现
        raise NotImplementedError("HTML 输出将在 v5.0 实现")
