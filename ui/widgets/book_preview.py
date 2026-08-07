# -*- coding: utf-8 -*-
"""EPUB 预览面板"""
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser
from PySide6.QtCore import Qt


class BookPreview(QWidget):
    """EPUB 内容预览"""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("📖 EPUB 预览")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 12px 20px;
            color: #fff;
            background: rgba(255, 255, 255, 0.05);
        """)
        layout.addWidget(title)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background: #1a1a1a;
                color: #ddd;
                font-size: 15px;
                padding: 24px;
                border: none;
            }
        """)
        layout.addWidget(self.text_browser)

    def set_content(self, html: str):
        """设置预览内容（HTML 格式）"""
        self.text_browser.setHtml(html)

    def set_plain_text(self, text: str):
        """设置纯文本预览"""
        self.text_browser.setPlainText(text)

    def load_epub(self, epub_path: str):
        """加载 EPUB 文件并预览

        提取 EPUB 中的 HTML 内容，拼接后显示。
        """
        if not os.path.exists(epub_path):
            self.set_plain_text(f"文件不存在: {epub_path}")
            return

        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup

            book = epub.read_epub(epub_path)
            html_parts = []

            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                # 提取 body 内容
                body = soup.find('body')
                if body:
                    html_parts.append(str(body))

            if html_parts:
                combined = '\n'.join(html_parts)
                # 限制预览长度
                if len(combined) > 50000:
                    combined = combined[:50000] + '\n<p style="color: #888;">... (预览已截断)</p>'
                self.set_content(combined)
            else:
                self.set_plain_text("EPUB 文件中未找到可预览的内容")

        except Exception as e:
            self.set_plain_text(f"加载失败: {e}")
