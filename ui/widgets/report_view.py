# -*- coding: utf-8 -*-
"""转换报告显示组件 — 卡片式统计 + 进度环"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt


class StatCard(QFrame):
    """单个统计卡片"""

    def __init__(self, icon: str, label: str, value: str, color: str = "#0078d4"):
        super().__init__()
        self.setFixedHeight(72)
        self.setStyleSheet(f"""
            StatCard, QFrame {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid #333;
                border-radius: 10px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        # 图标
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f"font-size: 24px;")
        lbl_icon.setFixedWidth(32)
        layout.addWidget(lbl_icon)

        # 文字区
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        text_layout.addWidget(lbl_value)

        lbl_label = QLabel(label)
        lbl_label.setStyleSheet("font-size: 11px; color: #888;")
        text_layout.addWidget(lbl_label)

        layout.addLayout(text_layout)
        layout.addStretch()


class AccuracyRing(QFrame):
    """OCR 准确率环形进度指示器"""

    def __init__(self, accuracy: float):
        super().__init__()
        self.setFixedSize(100, 100)

        # 根据准确率选择颜色
        if accuracy >= 95:
            color = "#43e97b"  # 绿
        elif accuracy >= 85:
            color = "#4facfe"  # 蓝
        elif accuracy >= 70:
            color = "#fa709a"  # 橙粉
        else:
            color = "#f5576c"  # 红

        pct = int(accuracy)

        self.setStyleSheet(f"""
            AccuracyRing, QFrame {{
                border-radius: 50px;
                border: 4px solid #333;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl_pct = QLabel(f"{pct}%")
        lbl_pct.setAlignment(Qt.AlignCenter)
        lbl_pct.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
        layout.addWidget(lbl_pct)

        lbl_label = QLabel("准确率")
        lbl_label.setAlignment(Qt.AlignCenter)
        lbl_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(lbl_label)


class ReportView(QWidget):
    """转换报告 — 卡片式布局"""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("📊 转换报告")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 0;")
        layout.addWidget(title)

        # 文件信息
        self._info_frame = QFrame()
        self._info_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid #333;
                border-radius: 8px;
            }
        """)
        info_layout = QVBoxLayout(self._info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(6)

        self._lbl_source = QLabel()
        self._lbl_source.setStyleSheet("font-size: 13px; color: #ccc;")
        self._lbl_source.setWordWrap(True)
        info_layout.addWidget(self._lbl_source)

        self._lbl_output = QLabel()
        self._lbl_output.setStyleSheet("font-size: 13px; color: #ccc;")
        self._lbl_output.setWordWrap(True)
        info_layout.addWidget(self._lbl_output)

        layout.addWidget(self._info_frame)

        # OCR 准确率 + 统计卡片行
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        # 准确率环
        self._accuracy_ring = QLabel("等待数据...")
        self._accuracy_ring.setFixedSize(100, 100)
        self._accuracy_ring.setAlignment(Qt.AlignCenter)
        stats_row.addWidget(self._accuracy_ring)

        # 统计卡片网格 2x3
        cards_widget = QWidget()
        cards_layout = QVBoxLayout(cards_widget)
        cards_layout.setSpacing(8)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self._card_pages = StatCard("📄", "总页数", "0")
        self._card_paras = StatCard("📝", "段落", "0")
        self._card_chapters = StatCard("📑", "章节", "0")
        self._card_chars = StatCard("🔤", "字数", "0")
        self._card_images = StatCard("🖼️", "图片", "0")
        self._card_errors = StatCard("⚠️", "错误字符", "0", "#f5576c")

        row1.addWidget(self._card_pages)
        row1.addWidget(self._card_paras)
        row1.addWidget(self._card_chapters)
        row2.addWidget(self._card_chars)
        row2.addWidget(self._card_images)
        row2.addWidget(self._card_errors)

        cards_layout.addLayout(row1)
        cards_layout.addLayout(row2)
        stats_row.addWidget(cards_widget, 1)

        layout.addLayout(stats_row)

        # 耗时
        self._lbl_duration = QLabel()
        self._lbl_duration.setStyleSheet("""
            font-size: 14px;
            color: #888;
            padding: 8px 0;
        """)
        layout.addWidget(self._lbl_duration)

        layout.addStretch()

    def set_report(self, data: dict):
        """设置报告数据"""
        filename = data.get('filename', '—')
        output_path = data.get('output_path', '—')
        self._lbl_source.setText(f"<b>源文件：</b>{filename}")
        self._lbl_output.setText(f"<b>输出文件：</b>{output_path}")

        # 更新卡片
        self._card_pages = self._replace_card(self._card_pages, "📄", "总页数", str(data.get('total_pages', 0)))
        self._card_paras = self._replace_card(self._card_paras, "📝", "段落", str(data.get('total_paragraphs', 0)))
        self._card_chapters = self._replace_card(self._card_chapters, "📑", "章节", str(data.get('chapters', 0)))
        self._card_chars = self._replace_card(self._card_chars, "🔤", "字数", str(data.get('total_chars', 0)))
        self._card_images = self._replace_card(self._card_images, "🖼️", "图片", str(data.get('images', 0)))
        self._card_errors = self._replace_card(self._card_errors, "⚠️", "错误字符", str(data.get('errors', 0)), "#f5576c")

        # 准确率环
        accuracy = data.get('accuracy', 0)
        if accuracy >= 95:
            color = "#43e97b"
        elif accuracy >= 85:
            color = "#4facfe"
        elif accuracy >= 70:
            color = "#fa709a"
        else:
            color = "#f5576c"

        self._accuracy_ring.setText(
            f"<div style='text-align:center;'>"
            f"<div style='font-size:22px;font-weight:bold;color:{color};'>{int(accuracy)}%</div>"
            f"<div style='font-size:10px;color:#888;'>准确率</div>"
            f"</div>"
        )

        # 耗时
        duration = data.get('duration', '—')
        self._lbl_duration.setText(f"⏱️ 处理耗时：<b>{duration}</b>")

    def _replace_card(self, old_card: StatCard, icon: str, label: str, value: str, color: str = "#0078d4"):
        """替换统计卡片（更新值）"""
        old_card.deleteLater()
        new_card = StatCard(icon, label, value, color)
        # 找到 old_card 的父布局并替换
        parent = old_card.parentWidget()
        if parent:
            layout = parent.layout()
            idx = layout.indexOf(old_card)
            layout.removeWidget(old_card)
            layout.insertWidget(idx, new_card)
        return new_card
