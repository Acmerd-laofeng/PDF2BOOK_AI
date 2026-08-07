# -*- coding: utf-8 -*-
"""转换报告显示组件"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PySide6.QtCore import Qt


class ReportView(QWidget):
    """转换报告"""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("📊 转换报告")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #ddd;
                font-size: 14px;
                padding: 20px;
                border: none;
            }
        """)
        layout.addWidget(self.report_text)

    def set_report(self, data: dict):
        """设置报告数据

        Args:
            data: {
                "filename": str,
                "total_pages": int,
                "total_paragraphs": int,
                "total_chars": int,
                "chapters": int,
                "images": int,
                "errors": int,
                "accuracy": float,
                "duration": str,
                "output_path": str,
            }
        """
        html = f"""
        <div style="line-height: 2.0;">
        <h2>转换完成报告</h2>
        <hr/>
        <p><b>源文件：</b>{data.get('filename', '—')}</p>
        <p><b>输出文件：</b>{data.get('output_path', '—')}</p>
        <hr/>
        <p><b>总页数：</b>{data.get('total_pages', 0)}</p>
        <p><b>总段落：</b>{data.get('total_paragraphs', 0)}</p>
        <p><b>总字数：</b>{data.get('total_chars', 0)}</p>
        <p><b>章节数：</b>{data.get('chapters', 0)}</p>
        <p><b>图片数：</b>{data.get('images', 0)}</p>
        <hr/>
        <p><b>OCR 准确率：</b>{data.get('accuracy', 0):.1f}%</p>
        <p><b>错误字符：</b>{data.get('errors', 0)}</p>
        <p><b>处理耗时：</b>{data.get('duration', '—')}</p>
        </div>
        """
        self.report_text.setHtml(html)
