# -*- coding: utf-8 -*-
"""PDF2BOOK AI - 程序入口"""
import sys
import os

# 设置工作目录为脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# 高 DPI 支持
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

from app.bootstrap import Bootstrap
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # 设置全局字体
    app.setFont(QFont("Microsoft YaHei UI", 9))

    # 初始化（数据库、配置、目录）
    bootstrap = Bootstrap()
    bootstrap.init()

    # 设置暗色主题
    from qfluentwidgets import Theme, setTheme
    setTheme(Theme.DARK)

    # 加载自定义 QSS
    qss_path = os.path.join("ui", "theme", "dark.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(app.styleSheet() + f.read())

    # 启动主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
