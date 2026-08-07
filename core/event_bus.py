# -*- coding: utf-8 -*-
"""事件总线 - 基于 Qt Signal 的全局事件中心

所有核心引擎的事件通过此单例广播，
UI 组件通过 connect 自动响应。

信号清单：
    progress(str, int)          — 转换进度 (filename, percent)
    finished(str)               — 转换完成 filename
    error(str, str)             — 转换错误 (filename, error_msg)
    analysis_done(dict)         — PDF 分析结果
    task_status_changed(int, str) — 任务状态变化 (task_id, status)
    task_added(int)             — 新任务添加 task_id
    task_removed(int)           — 任务删除 task_id
    task_progress(int, int)     — 任务进度 (task_id, percent)
    report_ready(dict)          — 转换报告
    log_message(str)            — 日志消息
    book_added(int)             — 书库新增 book_id
    book_removed(int)           — 书库删除 book_id
    correction_learned(str, str) — 纠错学习 (wrong, correct)
"""
from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """全局事件总线"""

    # === 转换流程 ===
    progress = Signal(str, int)            # (filename, percent)
    finished = Signal(str)                 # filename
    error = Signal(str, str)               # (filename, error_msg)
    analysis_done = Signal(dict)           # PDF 分析结果
    report_ready = Signal(dict)            # 转换报告

    # === 任务管理 ===
    task_added = Signal(int)               # task_id
    task_removed = Signal(int)             # task_id
    task_status_changed = Signal(int, str) # (task_id, status)
    task_progress = Signal(int, int)       # (task_id, percent)

    # === 书库 ===
    book_added = Signal(int)               # book_id
    book_removed = Signal(int)             # book_id

    # === 纠错学习 ===
    correction_learned = Signal(str, str)  # (wrong, correct)

    # === 日志 ===
    log_message = Signal(str)              # 日志文本


# 全局单例
event_bus = EventBus()
