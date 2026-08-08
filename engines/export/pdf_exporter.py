# -*- coding: utf-8 -*-
"""PDF 导出器 — 将 ParsedDocument 导出为 PDF

使用 reportlab 生成 PDF。
"""
import os
from typing import List

from engines.exporter_base import BaseExporter
from engines.document import ParsedDocument, Chapter


class PDFExporter(BaseExporter):
    """PDF 导出器（基于 reportlab）"""

    def export(self, doc: ParsedDocument, output_path: str, options: dict = None) -> str:
        options = options or {}
        page_size = options.get("page_size", "A4")
        font_size = options.get("font_size", 12)

        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, PageBreak
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        # 注册中文字体
        self._register_chinese_font()

        page_sizes = {"A4": A4, "letter": letter}
        ps = page_sizes.get(page_size, A4)

        pdf_doc = SimpleDocTemplate(
            output_path,
            pagesize=ps,
            leftMargin=25 * mm,
            rightMargin=25 * mm,
            topMargin=25 * mm,
            bottomMargin=25 * mm,
        )

        styles = getSampleStyleSheet()

        # 自定义样式
        font_name = "STSong" if self._has_chinese_font else "Helvetica"
        title_style = ParagraphStyle(
            "ChineseTitle",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=font_size + 6,
            alignment=TA_CENTER,
            spaceAfter=20 * mm,
        )
        heading_style = ParagraphStyle(
            "ChineseHeading",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=font_size + 4,
            alignment=TA_CENTER,
            spaceBefore=15 * mm,
            spaceAfter=8 * mm,
        )
        body_style = ParagraphStyle(
            "ChineseBody",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=font_size,
            leading=font_size * 1.8,
            firstLineIndent=font_size * 2,
            spaceAfter=3 * mm,
            alignment=TA_LEFT,
        )

        story = []

        # 书名
        if doc.title:
            story.append(Paragraph(self._escape(doc.title), title_style))

        # 作者
        if doc.author and doc.author != "Unknown":
            author_style = ParagraphStyle(
                "Author", parent=body_style, alignment=TA_CENTER,
                firstLineIndent=0, fontSize=font_size, textColor="#666666"
            )
            story.append(Paragraph(self._escape(doc.author), author_style))
            story.append(Spacer(1, 15 * mm))

        # 章节
        for chapter in doc.chapters:
            if chapter.title:
                story.append(Paragraph(self._escape(chapter.title), heading_style))

            for para in chapter.paragraphs:
                if para.strip():
                    story.append(Paragraph(self._escape(para), body_style))

            story.append(PageBreak())

        # 移除最后一个 PageBreak
        if story and isinstance(story[-1], PageBreak):
            story.pop()

        pdf_doc.build(story)
        return output_path

    def _register_chinese_font(self):
        """注册中文字体"""
        self._has_chinese_font = False

        # 尝试常见中文字体路径
        font_paths = [
            ("STSong", "C:/Windows/Fonts/simsun.ttc"),
            ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
            ("MSYH", "C:/Windows/Fonts/msyh.ttc"),
            ("SimHei", "C:/Windows/Fonts/simhei.ttf"),
        ]

        for font_name, font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self._has_chinese_font = True
                    self._font_name = font_name
                    return
                except Exception:
                    continue

    @staticmethod
    def _escape(text: str) -> str:
        """HTML 转义（reportlab Paragraph 需要）"""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text
