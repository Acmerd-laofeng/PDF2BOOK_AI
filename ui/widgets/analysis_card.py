# -*- coding: utf-8 -*-
"""PDF 智能分析卡片组件"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt



class AnalysisCard(QFrame):
    """PDF 智能分析结果卡片

    显示字段：文件名、页数、类型（文字版/扫描版/混合）、文字页数、
    图片页数、文件大小、预估耗时、是否含目录。
    """

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            AnalysisCard, QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 20px;
            }
            QLabel { font-size: 14px; color: #ccc; }
            QLabel#title { font-size: 18px; font-weight: bold; color: #fff; }
            QLabel#value { font-size: 16px; color: #60cdff; font-weight: bold; }
            QLabel#label { font-size: 13px; color: #888; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 标题
        title = QLabel("📋 PDF 智能分析")
        title.setObjectName("title")
        layout.addWidget(title)

        # 文件名行
        self.lbl_filename = QLabel("—")
        self.lbl_filename.setStyleSheet("font-size: 15px; color: #fff; font-weight: bold;")
        layout.addWidget(self.lbl_filename)

        # 信息网格 2 列
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(0, 8, 0, 0)

        self.lbl_pages = self._add_grid_row(grid, 0, 0, "页面数量")
        self.lbl_type = self._add_grid_row(grid, 0, 1, "PDF 类型")
        self.lbl_text_pages = self._add_grid_row(grid, 1, 0, "文字页数")
        self.lbl_image_pages = self._add_grid_row(grid, 1, 1, "图片页数")
        self.lbl_size = self._add_grid_row(grid, 2, 0, "文件大小")
        self.lbl_est_time = self._add_grid_row(grid, 2, 1, "预计耗时")
        self.lbl_has_toc = self._add_grid_row(grid, 3, 0, "内置目录")

        layout.addLayout(grid)

    def _add_grid_row(self, grid, row, col, label_text):
        """在网格中添加一行信息，返回值 QLabel"""
        col_layout = QVBoxLayout()
        col_layout.setSpacing(2)

        lbl = QLabel(label_text)
        lbl.setObjectName("label")
        col_layout.addWidget(lbl)

        value = QLabel("—")
        value.setObjectName("value")
        col_layout.addWidget(value)

        grid.addLayout(col_layout, row, col)
        return value

    def update_info(self, info: dict):
        """更新分析结果

        analyzer.analyze() 返回字段:
            pages, type, text_pages, image_pages, page_size, file_size, has_toc
        外部补充: filename, size, est_time, language
        """
        import os

        # 文件名
        filename = info.get("filename", "")
        if not filename and "path" in info:
            filename = os.path.basename(info["path"])
        self.lbl_filename.setText(filename or "—")

        # 类型
        pdf_type = info.get("type", "—")
        type_map = {"text": "文字版", "scan": "扫描版", "mixed": "混合版"}
        self.lbl_type.setText(type_map.get(pdf_type, pdf_type))

        # 页数
        self.lbl_pages.setText(str(info.get("pages", "—")))
        self.lbl_text_pages.setText(str(info.get("text_pages", "—")))
        self.lbl_image_pages.setText(str(info.get("image_pages", "—")))

        # 文件大小
        self.lbl_size.setText(info.get("size", info.get("file_size", "—")))

        # 预估耗时
        self.lbl_est_time.setText(info.get("est_time", "—"))

        # 目录
        has_toc = info.get("has_toc", False)
        self.lbl_has_toc.setText("✅ 有" if has_toc else "❌ 无")
