# -*- coding: utf-8 -*-
"""PDF 页面渲染器"""
import fitz
from typing import Optional


class Renderer:
    """将 PDF 页面渲染为图片

    支持 DPI 设置，越高越精准但越慢。
    支持渲染为 Pixmap、字节、文件。
    """

    def __init__(self):
        self._last_dpi = 300

    def render(self, page, dpi: int = 300) -> fitz.Pixmap:
        """渲染页面为 pixmap

        Args:
            page: PyMuPDF page 对象
            dpi: 渲染 DPI

        Returns:
            fitz.Pixmap
        """
        self._last_dpi = dpi
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        return page.get_pixmap(matrix=mat)

    def render_to_bytes(self, page, dpi: int = 300, fmt: str = "png") -> bytes:
        """渲染为图片字节"""
        pix = self.render(page, dpi)
        return pix.tobytes(fmt)

    def render_to_file(self, page, output_path: str, dpi: int = 300):
        """渲染到文件"""
        pix = self.render(page, dpi)
        pix.save(output_path)

    def render_clip(self, page, clip_rect: fitz.Rect, dpi: int = 300) -> fitz.Pixmap:
        """渲染页面指定区域（用于图片提取）

        Args:
            page: PyMuPDF page 对象
            clip_rect: 裁剪区域
            dpi: 渲染 DPI
        """
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        return page.get_pixmap(matrix=mat, clip=clip_rect)

    @property
    def last_dpi(self) -> int:
        return self._last_dpi
