# -*- coding: utf-8 -*-
"""我的书库 - 书籍卡片网格"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QHBoxLayout
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, BodyLabel, PushButton, FluentIcon as FIF,
    InfoBar, InfoBarPosition, SearchLineEdit,
)

from ui.widgets.book_card import BookCard


class LibraryPage(QWidget):
    """我的书库"""

    def __init__(self):
        super().__init__()
        self._books = []
        self._all_books_data = []  # 数据库原始数据缓存（用于搜索过滤）
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # 标题行
        header = QHBoxLayout()
        header.addWidget(TitleLabel("我的书库"))
        header.addStretch()

        # 搜索框
        self.search_box = SearchLineEdit()
        self.search_box.setPlaceholderText("搜索书名...")
        self.search_box.setFixedWidth(220)
        self.search_box.textChanged.connect(self._on_search)
        header.addWidget(self.search_box)

        self.btn_refresh = PushButton("刷新")
        self.btn_refresh.setIcon(FIF.SYNC)
        self.btn_refresh.clicked.connect(self.load_from_db)
        header.addWidget(self.btn_refresh)
        layout.addLayout(header)

        # 统计
        self.lbl_count = BodyLabel("共 0 本")
        self.lbl_count.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.lbl_count)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        # 空状态
        self.lbl_empty = BodyLabel("📚 书库为空，转换完成后会自动添加")
        self.lbl_empty.setStyleSheet("color: #666; font-size: 16px; padding: 60px;")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(self.lbl_empty, 0, 0)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def add_book(self, title: str, author: str = "未知", epub_path: str = ""):
        """添加书籍卡片"""
        if self.lbl_empty.isVisible():
            self.lbl_empty.setVisible(False)

        card = BookCard(title, author, epub_path)
        card.clicked.connect(self._on_book_clicked)
        card.delete_requested.connect(self._on_book_delete)
        card.open_dir_requested.connect(self._on_book_open_dir)

        row = len(self._books) // 5
        col = len(self._books) % 5
        self.grid_layout.addWidget(card, row, col)
        self._books.append(card)

        self._update_count()

    def load_from_db(self):
        """从数据库加载书库"""
        # 清空现有
        self.clear_books()

        try:
            from database.db import Database
            db = Database()
            rows = db.fetch_all(
                "SELECT title, author, output_epub FROM books ORDER BY created_time DESC"
            )
            db.close()

            self._all_books_data = rows or []

            if rows:
                for row in rows:
                    title, author, epub_path = row[0], row[1], row[2] or ""
                    self.add_book(title, author or "未知", epub_path)
            else:
                self.lbl_empty.setVisible(True)
        except Exception as e:
            self.lbl_empty.setText(f"加载失败: {e}")
            self.lbl_empty.setVisible(True)

    def _on_search(self, text: str):
        """搜索过滤"""
        text = text.strip().lower()
        self.clear_books()

        if not text:
            # 无搜索词：显示全部
            for row in self._all_books_data:
                title, author, epub_path = row[0], row[1], row[2] or ""
                self.add_book(title, author or "未知", epub_path)
        else:
            # 过滤匹配
            matched = [
                row for row in self._all_books_data
                if text in (row[0] or "").lower() or text in (row[1] or "").lower()
            ]
            if matched:
                for row in matched:
                    title, author, epub_path = row[0], row[1], row[2] or ""
                    self.add_book(title, author or "未知", epub_path)
            else:
                self.lbl_empty.setText("🔍 未找到匹配书籍")
                self.lbl_empty.setVisible(True)

    def _on_book_clicked(self, title: str):
        """点击书籍 → 预览"""
        for card in self._books:
            if card.title == title:
                epub_path = getattr(card, "epub_path", "")
                if epub_path:
                    self._show_preview(epub_path, title)
                break

    def _show_preview(self, epub_path: str, title: str):
        """显示预览弹窗"""
        from ui.widgets.book_preview import BookPreview
        from PySide6.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle(f"预览 - {title}")
        dialog.setMinimumSize(600, 700)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        preview = BookPreview()
        preview.load_epub(epub_path)
        layout.addWidget(preview)

        dialog.exec()

    def _on_book_delete(self, title: str):
        """删除书籍"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要从书库中删除「{title}」吗？\n（不会删除磁盘上的文件）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        for i, card in enumerate(self._books):
            if card.title == title:
                # 从数据库删除
                try:
                    from database.db import Database
                    db = Database()
                    db.execute("DELETE FROM books WHERE title = ?", (title,))
                    db.close()
                except Exception:
                    pass

                self.grid_layout.removeWidget(card)
                card.deleteLater()
                self._books.pop(i)
                break

        # 重新排列
        for i, card in enumerate(self._books):
            self.grid_layout.removeWidget(card)
            row = i // 5
            col = i % 5
            self.grid_layout.addWidget(card, row, col)

        if not self._books:
            self.lbl_empty.setVisible(True)

        self._update_count()

    def _on_book_open_dir(self, title: str):
        """打开书籍所在目录"""
        import subprocess, os
        for card in self._books:
            if card.title == title:
                epub_path = getattr(card, "epub_path", "")
                if epub_path and os.path.exists(os.path.dirname(epub_path)):
                    subprocess.Popen(f'explorer /select,"{epub_path}"')
                else:
                    from qfluentwidgets import InfoBar, InfoBarPosition
                    InfoBar.warning(
                        title="路径不存在",
                        content=f"文件路径不存在: {epub_path}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self,
                    )
                break

    def clear_books(self):
        """清空书库"""
        for card in self._books:
            card.deleteLater()
        self._books.clear()
        self.lbl_empty.setVisible(True)
        self._update_count()

    def _update_count(self):
        self.lbl_count.setText(f"共 {len(self._books)} 本")
