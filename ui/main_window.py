# -*- coding: utf-8 -*-
"""主窗口 - FluentWindow + 左侧导航 + 事件连接"""
import os
from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    MessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from ui.pages.home_page import HomePage
from ui.pages.convert_page import ConvertPage
from ui.pages.library_page import LibraryPage
from ui.pages.task_page import TaskPage
from ui.pages.setting_page import SettingPage
from ui.dialogs.report_dialog import ReportDialog
from core.event_bus import event_bus
from core.models import Task, ConvertSettings
from app.constants import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, UPDATE_ENABLED


class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(900, 600)

        # 设置窗口图标
        icon_path = os.path.join("resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._current_pdf = None
        self._converter_service = None
        self._task_reports = {}  # task_id → report_data

        self._init_pages()
        self._init_navigation()
        self._connect_events()

        # 启动后延迟 2 秒检查更新（不阻塞启动）
        if UPDATE_ENABLED:
            QTimer.singleShot(2000, self._check_update)

    def _init_pages(self):
        """创建所有页面"""
        self.home_page = HomePage()
        self.home_page.setObjectName("home_page")
        self.convert_page = ConvertPage()
        self.convert_page.setObjectName("convert_page")
        self.library_page = LibraryPage()
        self.library_page.setObjectName("library_page")
        self.task_page = TaskPage()
        self.task_page.setObjectName("task_page")
        self.setting_page = SettingPage()
        self.setting_page.setObjectName("setting_page")

    def _init_navigation(self):
        """配置左侧导航栏"""
        self.addSubInterface(self.home_page, FluentIcon.HOME, "首页")
        self.addSubInterface(self.convert_page, FluentIcon.DOCUMENT, "转换")
        self.addSubInterface(self.library_page, FluentIcon.BOOK_SHELF, "书库")
        self.addSubInterface(self.task_page, FluentIcon.SYNC, "任务")
        self.addSubInterface(
            self.setting_page, FluentIcon.SETTING, "设置",
            NavigationItemPosition.BOTTOM
        )

    def _connect_events(self):
        """连接全局事件"""
        # EventBus 信号 → UI 更新
        event_bus.progress.connect(self._on_progress)
        event_bus.finished.connect(self._on_finished)
        event_bus.error.connect(self._on_error)
        event_bus.task_status_changed.connect(self._on_task_status)
        event_bus.analysis_done.connect(self._on_analysis_done)
        event_bus.task_added.connect(self._on_task_added)
        event_bus.report_ready.connect(self._on_report_ready)

        # 首页信号
        self.home_page.file_selected.connect(self._on_file_selected)
        self.home_page.start_convert.connect(self._on_start_convert)

        # 转换页信号
        self.convert_page.start_conversion.connect(self._on_convert_started)

        # 任务页信号
        self.task_page.cancel_task.connect(self._on_cancel_task)

        # 设置页信号
        self.setting_page.settings_changed.connect(self._on_settings_changed)

    # --- EventBus 事件处理 ---

    def _on_progress(self, filename: str, percent: int):
        """转换进度更新"""
        self.convert_page.update_progress(percent)
        self.task_page.update_progress_by_name(filename, percent)

    def _on_finished(self, filename: str):
        """转换完成"""
        InfoBar.success(
            "转换完成",
            f"{filename} 已成功转换",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000,
        )

        # 弹出报告弹窗（report_ready 信号已更新 _task_reports）
        for task_id, report in self._task_reports.items():
            if report.get("filename") == filename and len(report) > 1:
                dialog = ReportDialog(report, self)
                dialog.exec()
                break

        # 刷新书库
        self._refresh_library()

    def _on_error(self, filename: str, error_msg: str):
        """转换错误"""
        InfoBar.error(
            "转换失败",
            f"{filename}: {error_msg}",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=8000,
        )

    def _on_task_status(self, task_id: int, status: str):
        """任务状态变化"""
        self.task_page.update_task(task_id, status, 0)

    def _on_analysis_done(self, info: dict):
        """PDF 分析完成"""
        self.home_page.show_analysis(info)

    def _on_task_added(self, task_id: int):
        """新任务添加"""
        pass

    def _on_report_ready(self, report: dict):
        """转换报告就绪 → 缓存报告数据"""
        # 通过 filename 匹配 task_id
        filename = report.get("filename", "")
        for task_id, data in self._task_reports.items():
            if data.get("filename") == filename:
                self._task_reports[task_id] = report
                break

    # --- UI 事件处理 ---

    def _on_file_selected(self, file_path: str):
        """用户选择了 PDF 文件"""
        self._current_pdf = file_path

        # 后台线程分析 PDF（避免大文件卡 UI）
        from PySide6.QtCore import QThread, Signal as QSignal

        class AnalyzeThread(QThread):
            result = QSignal(dict)
            error = QSignal(str)

            def __init__(self, path):
                super().__init__()
                self.path = path

            def run(self):
                try:
                    from engines.pdf.analyzer import PDFAnalyzer
                    analyzer = PDFAnalyzer()
                    info = analyzer.analyze(self.path)
                    # 补充文件大小格式化
                    size = os.path.getsize(self.path)
                    if size < 1024:
                        info["size"] = f"{size} B"
                    elif size < 1024 * 1024:
                        info["size"] = f"{size / 1024:.1f} KB"
                    else:
                        info["size"] = f"{size / 1024 / 1024:.1f} MB"
                    # 预估时间
                    pages = info.get("pages", 0)
                    if info.get("type") == "text":
                        info["est_time"] = f"{max(1, pages // 20)} 秒"
                    else:
                        info["est_time"] = f"{max(1, pages * 5 // 60)} 分钟"
                    self.result.emit(info)
                except Exception as e:
                    self.error.emit(str(e))

        self._analyze_thread = AnalyzeThread(file_path)
        self._analyze_thread.result.connect(self.home_page.show_analysis)
        self._analyze_thread.error.connect(
            lambda msg: InfoBar.error("分析失败", msg, parent=self, duration=5000)
        )
        self._analyze_thread.start()

    def _on_start_convert(self):
        """首页"开始转换"按钮 → 跳转转换页"""
        if not self._current_pdf:
            InfoBar.warning("提示", "请先选择 PDF 文件", parent=self)
            return
        self.navigate_to("convert")
        self.convert_page.set_pdf_info(self._current_pdf)

    def _on_convert_started(self, settings: dict):
        """转换页开始转换"""
        if not self._current_pdf:
            InfoBar.warning("提示", "请先在首页选择 PDF 文件", parent=self)
            self.navigate_to("home")
            return

        filename = os.path.basename(self._current_pdf)

        from core.converter import ConverterService
        service = ConverterService()
        self._converter_service = service

        task = service.create_task(filename, self._current_pdf, settings)
        self._task_reports[task.id] = {"filename": filename}

        # 在任务页添加卡片
        self.task_page.add_task(task.id, filename)
        # 在首页添加最近任务
        self.home_page.add_recent_task(filename)

        # 跳转到任务页
        self.navigate_to("task")

        # 启动转换
        service.start_task(task)

    def _on_cancel_task(self, task_id: int):
        """取消任务"""
        if self._converter_service:
            self._converter_service.cancel_task(task_id)
        self.task_page.update_task(task_id, "cancelled", 0)

    def _on_settings_changed(self, settings: dict):
        """设置页保存设置（setting_page 已自行持久化，此处仅做 UI 反馈）"""
        InfoBar.success("设置已保存", "", parent=self, duration=2000)

    def _refresh_library(self):
        """刷新书库"""
        self.library_page.load_from_db()

    def navigate_to(self, page_name: str):
        """编程式导航跳转"""
        page_map = {
            "home": self.home_page,
            "convert": self.convert_page,
            "library": self.library_page,
            "task": self.task_page,
            "setting": self.setting_page,
        }
        page = page_map.get(page_name)
        if page:
            self.stackedWidget.setCurrentWidget(page)

    # --- 自动更新 ---

    def _check_update(self):
        """检查更新（后台线程，不阻塞 UI）"""
        from PySide6.QtCore import QThread, Signal as QSignal

        class CheckThread(QThread):
            result = QSignal(object)  # UpdateInfo or None

            def run(self):
                from core.updater import check_update
                info = check_update(timeout=5)
                self.result.emit(info)

        self._check_thread = CheckThread()
        self._check_thread.result.connect(self._on_update_checked)
        self._check_thread.start()

    def _on_update_checked(self, info):
        """更新检查完成"""
        if info is None:
            return  # 请求失败，静默跳过
        if not info.has_update:
            return  # 已是最新版本

        from ui.dialogs.update_dialog import UpdateDialog
        dialog = UpdateDialog(info, self)
        dialog.exec()
