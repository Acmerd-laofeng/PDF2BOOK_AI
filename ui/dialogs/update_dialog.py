# -*- coding: utf-8 -*-
"""更新提示弹窗 — 发现新版本时弹出，支持下载+静默安装"""
import os
import sys
import subprocess
import tempfile
from PySide6.QtCore import Qt, QThread, Signal as QSignal, QUrl, QFile, QIODevice
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextBrowser,
)
from qfluentwidgets import PushButton, FluentIcon as FIF, InfoBar, InfoBarPosition
from core.updater import UpdateInfo


class DownloadThread(QThread):
    """下载安装包线程（用 QNetworkAccessManager）"""
    progress = QSignal(int)          # 进度百分比
    finished = QSignal(str)          # 下载完成，参数=本地文件路径
    error = QSignal(str)             # 下载失败

    def __init__(self, url: str, save_path: str):
        super().__init__()
        self._url = url
        self._save_path = save_path
        self._nam = None
        self._reply = None
        self._file = None

    def run(self):
        self._nam = QNetworkAccessManager()
        self._file = QFile(self._save_path)
        if not self._file.open(QIODevice.WriteOnly):
            self.error.emit(f"无法创建文件: {self._save_path}")
            return

        req = QNetworkRequest(QUrl(self._url))
        req.setHeader(QNetworkRequest.UserAgentHeader, "PDF2BOOK-AI")
        self._reply = self._nam.get(req)

        self._reply.readyRead.connect(self._on_ready_read)
        self._reply.downloadProgress.connect(self._on_progress)
        self._reply.finished.connect(self._on_finished)
        self._reply.errorOccurred.connect(self._on_error)

        # 进入事件循环等待下载完成
        self.exec()

    def _on_ready_read(self):
        if self._reply and self._file:
            self._file.write(self._reply.readAll())

    def _on_progress(self, received: int, total: int):
        if total > 0:
            percent = int(received * 100 / total)
            self.progress.emit(percent)

    def _on_finished(self):
        if self._file:
            self._file.close()
        if self._reply:
            self._reply.deleteLater()
        self.quit()

        # 检查文件是否下载成功
        if os.path.exists(self._save_path) and os.path.getsize(self._save_path) > 1024 * 1024:
            self.finished.emit(self._save_path)
        else:
            self.error.emit("下载文件大小异常，可能下载不完整")

    def _on_error(self, error_code):
        if self._file:
            self._file.close()
        self.error.emit(f"网络错误 (code={error_code})")

    def cancel(self):
        """取消下载"""
        if self._reply:
            self._reply.abort()
        if self._file:
            self._file.close()
        self.quit()


class UpdateDialog(QDialog):
    """发现新版本弹窗

    显示版本号 + 更新日志 + 下载安装进度
    """

    def __init__(self, update_info: UpdateInfo, parent=None):
        super().__init__(parent)
        self._info = update_info
        self._download_thread = None
        self._installer_path = ""
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("发现新版本")
        self.setMinimumSize(480, 420)
        self.setStyleSheet("background: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        # 标题
        from app.constants import APP_VERSION
        title = QLabel(f"<h2>发现新版本 v{self._info.latest_version}</h2>")
        title.setStyleSheet("color: #0078d4;")
        layout.addWidget(title)

        subtitle = QLabel(f"当前版本 v{APP_VERSION}")
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        # 更新日志
        notes_label = QLabel("更新日志：")
        notes_label.setStyleSheet("color: #ccc; margin-top: 8px;")
        layout.addWidget(notes_label)

        notes_view = QTextBrowser()
        notes_view.setStyleSheet(
            "background: #252525; border: 1px solid #333; border-radius: 6px; color: #ddd;"
        )
        notes_view.setOpenExternalLinks(True)
        notes_view.setMarkdown(self._info.release_notes or "（无更新日志）")
        notes_view.setMinimumHeight(180)
        layout.addWidget(notes_view)

        # 进度条（默认隐藏）
        self._progress = QProgressBar()
        self._progress.setStyleSheet(
            "QProgressBar { background: #252525; border: 1px solid #333; border-radius: 4px; text-align: center; color: #ccc; }"
            "QProgressBar::chunk { background: #0078d4; border-radius: 3px; }"
        )
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # 状态标签
        self._status = QLabel("")
        self._status.setStyleSheet("color: #888;")
        self._status.setVisible(False)
        layout.addWidget(self._status)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_layout.addStretch()

        self._later_btn = PushButton("以后再说")
        self._later_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._later_btn)

        self._update_btn = PushButton("立即更新")
        self._update_btn.setStyleSheet(
            "Pushbutton { background: #0078d4; color: white; }"
        )
        self._update_btn.clicked.connect(self._start_download)
        btn_layout.addWidget(self._update_btn)

        layout.addLayout(btn_layout)

    def _start_download(self):
        """开始下载安装包"""
        if not self._info.download_url:
            # 没有直接下载链接，打开浏览器
            import webbrowser
            webbrowser.open(self._info.html_url or self._info.download_url)
            self.accept()
            return

        # 准备临时文件
        temp_dir = tempfile.gettempdir()
        self._installer_path = os.path.join(
            temp_dir,
            f"PDF2BOOK_AI_Setup_v{self._info.latest_version}.exe"
        )

        # 切换 UI 状态
        self._update_btn.setEnabled(False)
        self._update_btn.setText("下载中...")
        self._later_btn.setText("取消")
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._status.setVisible(True)
        self._status.setText("正在下载安装包...")

        # 断开之前的取消连接，重新连接到取消下载
        try:
            self._later_btn.clicked.disconnect()
        except RuntimeError:
            pass
        self._later_btn.clicked.connect(self._cancel_download)

        # 启动下载
        self._download_thread = DownloadThread(
            self._info.download_url, self._installer_path
        )
        self._download_thread.progress.connect(self._on_download_progress)
        self._download_thread.finished.connect(self._on_download_finished)
        self._download_thread.error.connect(self._on_download_error)
        self._download_thread.start()

    def _on_download_progress(self, percent: int):
        self._progress.setValue(percent)
        self._status.setText(f"正在下载安装包... {percent}%")

    def _on_download_finished(self, file_path: str):
        """下载完成，启动静默安装"""
        self._progress.setValue(100)
        self._status.setText("下载完成，正在安装...")

        # 启动安装程序（静默模式）
        # /SILENT: 静默安装（显示进度但不需用户交互）
        # /NORESTART: 安装程序不自行重启（我们手动重启）
        try:
            subprocess.Popen(
                [file_path, "/SILENT", "/NORESTART", "/CLOSEAPPLICATIONS"],
                close_fds=True,
            )
        except Exception as e:
            self._status.setText(f"启动安装失败: {e}")
            return

        # 当前程序退出，让安装程序接管
        self._status.setText("安装程序已启动，本软件将退出并安装...")
        # 延迟 1 秒退出，让用户看到提示
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, self._quit_and_install)

    def _on_download_error(self, error_msg: str):
        """下载失败"""
        self._progress.setVisible(False)
        self._status.setText(f"下载失败: {error_msg}")
        self._update_btn.setEnabled(True)
        self._update_btn.setText("重试下载")
        self._later_btn.setText("关闭")

        try:
            self._later_btn.clicked.disconnect()
        except RuntimeError:
            pass
        self._later_btn.clicked.connect(self.reject)

    def _cancel_download(self):
        """取消下载"""
        if self._download_thread:
            self._download_thread.cancel()
            self._download_thread.wait(3000)
        self.reject()

    def _quit_and_install(self):
        """退出程序，让安装程序完成安装"""
        if self.parent():
            self.parent().close()
        import sys
        sys.exit(0)
