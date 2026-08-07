# -*- coding: utf-8 -*-
"""PDF 读取封装"""
import fitz


class PDFReader:
    """PDF 读取器

    封装 PyMuPDF，提供页面访问接口。
    支持 context manager 和迭代器模式。
    """

    def __init__(self, pdf_path: str):
        self._doc = fitz.open(pdf_path)
        self._path = pdf_path
        self._total_pages = len(self._doc)

    @property
    def path(self) -> str:
        return self._path

    def count(self) -> int:
        """总页数"""
        return self._total_pages

    def get_page(self, page_num: int):
        """获取页面对象"""
        if page_num < 0 or page_num >= self._total_pages:
            raise IndexError(f"页码 {page_num} 超出范围 (0-{self._total_pages - 1})")
        return self._doc[page_num]

    def get_text(self, page_num: int) -> str:
        """获取页面文字层（如果有）"""
        return self._doc[page_num].get_text()

    def has_text_layer(self, page_num: int) -> bool:
        """检查指定页面是否有文字层"""
        text = self._doc[page_num].get_text().strip()
        return len(text) > 50

    def get_toc(self) -> list:
        """获取目录"""
        return self._doc.get_toc()

    def get_page_size(self, page_num: int = 0) -> tuple:
        """获取页面尺寸"""
        page = self._doc[page_num]
        return (page.rect.width, page.rect.height)

    def close(self):
        """关闭文档"""
        if self._doc:
            self._doc.close()
            self._doc = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __iter__(self):
        for i in range(self._total_pages):
            yield self._doc[i]

    def __len__(self):
        return self._total_pages
