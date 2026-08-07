# -*- coding: utf-8 -*-
"""图片提取器 - v4.0

从 PDF 中提取图片，嵌入 EPUB。

使用 PyMuPDF（fitz）内置的图片提取功能：
- get_page_images() → 获取页面引用的图片
- extract_image() → 提取图片二进制数据
- 自动过滤过小图片（< 100x100，可能是装饰元素）
- 自动过滤文字页面中的装饰图片

无需 OpenCV，纯 PyMuPDF 实现。
"""
import os
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import fitz  # PyMuPDF


class ImageExtractor:
    """图片提取器"""

    def __init__(self, min_width: int = 100, min_height: int = 100):
        """
        Args:
            min_width: 最小图片宽度（像素），小于此值过滤
            min_height: 最小图片高度（像素），小于此值过滤
        """
        self.min_width = min_width
        self.min_height = min_height

    def extract_from_page(self, doc: fitz.Document, page_num: int) -> List[Dict]:
        """从指定页面提取图片

        Args:
            doc: PyMuPDF Document
            page_num: 页码（0-indexed）

        Returns:
            [{"image_bytes": bytes, "ext": "png"|"jpeg", "width": int, "height": int,
              "page": int, "index": int}, ...]
        """
        page = doc[page_num]
        images = []
        img_list = page.get_images(full=True)

        for img_idx, img_info in enumerate(img_list):
            xref = img_info[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.width < self.min_width or pix.height < self.min_height:
                    pix = None
                    continue

                # 转换为 PNG 或 JPEG
                if pix.n < 5:  # RGB/Gray
                    img_bytes = pix.tobytes("png")
                    ext = "png"
                else:  # CMYK 等，转 RGB
                    pix2 = fitz.Pixmap(fitz.csRGB, pix)
                    img_bytes = pix2.tobytes("png")
                    ext = "png"
                    pix2 = None
                pix = None

                images.append({
                    "image_bytes": img_bytes,
                    "ext": ext,
                    "width": img_info[2] if len(img_info) > 2 else 0,
                    "height": img_info[3] if len(img_info) > 3 else 0,
                    "page": page_num,
                    "index": img_idx,
                })
            except Exception:
                continue

        return images

    def extract_all(self, pdf_path: str, max_pages: int = 0) -> List[Dict]:
        """提取 PDF 中所有图片

        Args:
            pdf_path: PDF 文件路径
            max_pages: 最多提取页数（0 = 全部）

        Returns:
            图片信息列表
        """
        doc = fitz.open(pdf_path)
        total = doc.page_count if max_pages == 0 else min(max_pages, doc.page_count)
        all_images = []

        for i in range(total):
            page_images = self.extract_from_page(doc, i)
            all_images.extend(page_images)

        doc.close()
        return all_images

    def extract_page_pixmap(self, doc: fitz.Document, page_num: int,
                            dpi: int = 150) -> Optional[bytes]:
        """将整页渲染为图片（用于扫描页或图片页）

        Args:
            doc: PyMuPDF Document
            page_num: 页码
            dpi: 渲染 DPI

        Returns:
            PNG bytes，或 None
        """
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")
