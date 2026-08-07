# -*- coding: utf-8 -*-
"""MOBI 输出（预留，v5 实现）"""


class MobiBuilder:
    """MOBI 格式生成器

    预留接口，未来通过 Calibre ebook-convert 转换。
    """

    def build(self, epub_path: str, output_path: str):
        """EPUB → MOBI 转换"""
        # TODO: v5 实现，调用 calibre ebook-convert
        raise NotImplementedError("MOBI 输出将在 v5.0 实现")
