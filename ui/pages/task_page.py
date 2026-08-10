# -*- coding: utf-8 -*-
"""任务中心 - 任务卡片列表 + 状态管理"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import (
    TitleLabel, BodyLabel, PushButton, FluentIcon as FIF
)

from ui.widgets.task_card import TaskCard


class TaskPage(QWidget):
    """任务中心"""

    cancel_task = Signal(int)  # task_id
    navigate_requested = Signal(str)  # 页面名

    def __init__(self):
        super().__init__()
        self._task_cards = {}  # task_id → TaskCard
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # 标题行
        header = QHBoxLayout()
        header.addWidget(TitleLabel("任务中心"))
        header.addStretch()

        self.btn_clear = PushButton("清空已完成")
        self.btn_clear.setIcon(FIF.DELETE)
        self.btn_clear.setEnabled(False)
        self.btn_clear.clicked.connect(self._on_clear_completed)
        header.addWidget(self.btn_clear)
        layout.addLayout(header)

        # 任务列表滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.task_container = QWidget()
        self.task_container.setStyleSheet("background: transparent;")
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setSpacing(12)
        self.task_layout.setContentsMargins(0, 0, 0, 0)

        # 空状态
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(16)

        self.lbl_empty = BodyLabel("📋 暂无转换任务")
        self.lbl_empty.setStyleSheet("color: #666; font-size: 16px;")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.lbl_empty)

        btn_go_convert = PushButton("去转换")
        btn_go_convert.setIcon(FIF.DOCUMENT)
        btn_go_convert.setFixedWidth(120)
        btn_go_convert.clicked.connect(lambda: self._navigate_to("convert"))
        empty_layout.addWidget(btn_go_convert, alignment=Qt.AlignCenter)

        self._empty_widget = empty_widget
        self.task_layout.addWidget(empty_widget)

        self.task_layout.addStretch()
        scroll.setWidget(self.task_container)
        layout.addWidget(scroll)

    def add_task(self, task_id: int, filename: str):
        """添加任务卡片"""
        if self._empty_widget.isVisible():
            self._empty_widget.setVisible(False)

        card = TaskCard(task_id, filename)
        card.cancel_clicked.connect(lambda tid: self.cancel_task.emit(tid))
        card.delete_clicked.connect(lambda tid: self._remove_task(tid))
        card.open_dir_clicked.connect(self._on_open_task_dir)
        self.task_layout.insertWidget(self.task_layout.count() - 1, card)
        self._task_cards[task_id] = card

    def update_task(self, task_id: int, status: str, progress: int):
        """更新任务状态"""
        card = self._task_cards.get(task_id)
        if card:
            card.update_status(status, progress)

        # 检查是否有已完成任务可清空
        has_completed = any(
            c._status in ("completed", "error", "cancelled")
            for c in self._task_cards.values()
        )
        self.btn_clear.setEnabled(has_completed)

    def update_progress_by_name(self, filename: str, percent: int):
        """通过文件名更新进度（用于 EventBus progress 信号）"""
        for card in self._task_cards.values():
            if card.filename == filename:
                card.update_progress(percent)
                break

    def _remove_task(self, task_id: int):
        """移除单个任务卡片"""
        card = self._task_cards.pop(task_id, None)
        if card:
            card.deleteLater()

        if not self._task_cards:
            self._empty_widget.setVisible(True)
            self.btn_clear.setEnabled(False)

    def _on_clear_completed(self):
        """清空已完成的任务"""
        to_remove = [
            tid for tid, card in self._task_cards.items()
            if card._status in ("completed", "error", "cancelled")
        ]
        for tid in to_remove:
            self._remove_task(tid)

    def get_task_count(self) -> int:
        return len(self._task_cards)

    def set_task_output(self, task_id: int, output_path: str):
        """设置任务输出路径"""
        card = self._task_cards.get(task_id)
        if card:
            card.set_output_path(output_path)

    def _on_open_task_dir(self, task_id: int):
        """打开任务输出目录"""
        import os, subprocess
        card = self._task_cards.get(task_id)
        if card and card._output_path:
            path = card._output_path
            if os.path.exists(path):
                if os.name == "nt":
                    subprocess.Popen(["explorer", "/select,", path])
                else:
                    subprocess.Popen(["xdg-open", os.path.dirname(path)])

    def _navigate_to(self, page: str):
        """触发导航信号"""
        self.navigate_requested.emit(page)
