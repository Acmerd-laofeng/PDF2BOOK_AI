# -*- coding: utf-8 -*-
"""PDF 分析弹窗 - 异步分析 + 进度显示"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt, QThread, Signal as QSignal
from qfluentwidgets import ProgressBar, PushButton, BodyLabel, TitleLabel


class AnalyzeThread(QThread):
    """PDF 分析线程"""
    step_done = QSignal(int, dict)  # step_num, partial_info
    finished = QSignal(dict)        # 完整分析结果
    error = QSignal(str)

    def __init__(self, pdf_path: str):
        super().__init__()
        self.pdf_path = pdf_path

    def run(self):
        try:
            from engines.pdf.analyzer import PDFAnalyzer

            # 步骤 1：文件读取
            size = os.path.getsize(self.pdf_path)
            self.step_done.emit(1, {"filename": os.path.basename(self.pdf_path)})

            # 步骤 2：页面检测
            analyzer = PDFAnalyzer()
            info = analyzer.analyze(self.pdf_path)

            # 补充文件大小
            if size < 1024:
                info["size"] = f"{size} B"
            elif size < 1024 * 1024:
                info["size"] = f"{size / 1024:.0f} KB"
            else:
                info["size"] = f"{size / 1024 / 1024:.1f} MB"
            self.step_done.emit(2, info)

            # 步骤 3：OCR 类型检测（已在 analyze 中完成）
            self.step_done.emit(3, info)

            # 步骤 4：图片检测（已在 analyze 中完成）
            self.step_done.emit(4, info)

            # 预估时间
            pages = info.get("pages", 0)
            if info.get("type") == "text":
                info["est_time"] = f"{max(1, pages // 20)} 秒"
            else:
                info["est_time"] = f"{max(1, pages * 5 // 60)} 分钟"

            self.finished.emit(info)

        except Exception as e:
            self.error.emit(str(e))


class PDFAnalyzerDialog(QDialog):
    """PDF 智能分析弹窗

    异步分析 PDF，显示步骤进度，完成后可开始转换。
    """

    start_convert = Signal(str)
    cancelled = Signal()

    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self._info = {}
        self._init_ui()
        self._start_analysis()

    def _init_ui(self):
        self.setWindowTitle("PDF 智能分析")
        self.setFixedSize(480, 400)
        self.setStyleSheet("background: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)

        title = TitleLabel("📋 正在分析 PDF...")
        layout.addWidget(title)

        filename = os.path.basename(self.pdf_path)
        lbl_file = BodyLabel(f"📄 {filename}")
        lbl_file.setStyleSheet("color: #888; font-size: 13px;")
        layout.addWidget(lbl_file)

        # 分析步骤
        self.steps = [
            BodyLabel("⏳ 文件读取..."),
            BodyLabel("⏳ 页面检测..."),
            BodyLabel("⏳ OCR 类型检测..."),
            BodyLabel("⏳ 图片检测..."),
        ]
        for lbl in self.steps:
            lbl.setStyleSheet("font-size: 14px; color: #888; padding: 2px 0;")
            layout.addWidget(lbl)

        # 进度条
        self.progress = ProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        layout.addStretch()

        # 按钮行
        btn_layout = QHBoxLayout()

        self.btn_cancel = PushButton("取消")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_start = PushButton("开始转换")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._on_start)
        btn_layout.addWidget(self.btn_start)

        layout.addLayout(btn_layout)

    def _start_analysis(self):
        """启动分析线程"""
        self._thread = AnalyzeThread(self.pdf_path)
        self._thread.step_done.connect(self._on_step_done)
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_step_done(self, step: int, info: dict):
        """步骤完成"""
        if 1 <= step <= 4:
            lbl = self.steps[step - 1]
            lbl.setText(lbl.text().replace("⏳", "✅"))
            lbl.setStyleSheet("font-size: 14px; color: #4caf50; padding: 2px 0;")
            self.progress.setValue(step * 25)

        self._info.update(info)

    def _on_finished(self, info: dict):
        """分析完成"""
        self._info = info
        self.btn_start.setEnabled(True)
        self.progress.setValue(100)

        # 更新标题
        title_label = self.findChild(TitleLabel)
        if title_label:
            title_label.setText("✅ 分析完成")

    def _on_error(self, msg: str):
        """分析失败"""
        for lbl in self.steps:
            if "⏳" in lbl.text():
                lbl.setText("❌ " + lbl.text().replace("⏳ ", ""))
                lbl.setStyleSheet("font-size: 14px; color: #f44336; padding: 2px 0;")
                break

        title_label = self.findChild(TitleLabel)
        if title_label:
            title_label.setText("❌ 分析失败")

        error_lbl = BodyLabel(f"错误: {msg}")
        error_lbl.setStyleSheet("color: #f44336; font-size: 13px;")
        self.layout().insertWidget(self.layout().count() - 2, error_lbl)

    def _on_start(self):
        self.start_convert.emit(self.pdf_path)
        self.accept()

    def _on_cancel(self):
        if hasattr(self, '_thread') and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait()
        self.cancelled.emit()
        self.reject()
