# -*- coding: utf-8 -*-
"""OCR 并行 Worker - v4.0

使用 QThreadPool 并行处理多页 OCR，提升 3-5x 速度。

设计：
- 每页一个 OcrRunnable 任务
- 通过 QThreadPool 限制并发数（默认 4）
- 结果通过 Signal 回传主线程
- 支持取消
"""
from typing import List, Optional
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from engines.ocr.base import OCRBlock
from engines.ocr.manager import OCRManager
from engines.pdf.renderer import Renderer
from engines.pdf.reader import PDFReader


class OcrTaskSignals(QObject):
    """OCR 任务信号"""
    page_done = Signal(int, list)    # (page_index, [OCRBlock, ...])
    page_error = Signal(int, str)    # (page_index, error_msg)
    all_done = Signal()              # 全部完成


class OcrRunnable(QRunnable):
    """单页 OCR 任务"""

    def __init__(self, page_index: int, img_bytes: bytes, ocr_manager: OCRManager):
        super().__init__()
        self.page_index = page_index
        self.img_bytes = img_bytes
        self.ocr_manager = ocr_manager
        self.signals = OcrTaskSignals()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    @Slot()
    def run(self):
        if self._cancelled:
            return
        try:
            result = self.ocr_manager.run(self.img_bytes)
            self.signals.page_done.emit(self.page_index, result)
        except Exception as e:
            self.signals.page_error.emit(self.page_index, str(e))


class ParallelOcrEngine:
    """并行 OCR 引擎

    使用 QThreadPool 并行处理多页 OCR。

    用法:
        engine = ParallelOcrEngine(thread_count=4)
        results = engine.run_parallel(pdf_reader, renderer, dpi=300, total_pages=100)
    """

    def __init__(self, thread_count: int = 4):
        self.thread_count = thread_count
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(thread_count)
        self._cancelled = False

    def cancel(self):
        """取消所有任务"""
        self._cancelled = True
        self.pool.clear()

    def run_parallel(self, pdf_reader: PDFReader, renderer: Renderer,
                     dpi: int, total_pages: int,
                     cached_pages: dict = None) -> dict:
        """并行 OCR

        Args:
            pdf_reader: PDF 读取器
            renderer: 页面渲染器
            dpi: 渲染 DPI
            total_pages: 总页数
            cached_pages: 已缓存的页 {page_index: [OCRBlock, ...]}

        Returns:
            {page_index: [OCRBlock, ...], ...}
        """
        if cached_pages is None:
            cached_pages = {}

        self._cancelled = False
        results = {}
        ocr_manager = OCRManager()

        # 先渲染所有页面（串行，因为 PyMuPDF 不是线程安全的）
        rendered_pages = {}
        tasks_to_ocr = []

        for i in range(total_pages):
            if self._cancelled:
                break
            if i in cached_pages:
                results[i] = cached_pages[i]
            else:
                page = pdf_reader.get_page(i)
                pix = renderer.render(page, dpi=dpi)
                img_bytes = pix.tobytes("png")
                rendered_pages[i] = img_bytes
                tasks_to_ocr.append(i)

        # 并行 OCR
        pending = len(tasks_to_ocr)
        if pending == 0:
            return results

        signals = OcrTaskSignals()
        completed = [0]

        def on_page_done(idx, blocks):
            results[idx] = blocks
            completed[0] += 1

        def on_page_error(idx, err):
            results[idx] = []
            completed[0] += 1

        def on_all_done():
            pass

        signals.page_done.connect(on_page_done)
        signals.page_error.connect(on_page_error)
        signals.all_done.connect(on_all_done)

        for idx in tasks_to_ocr:
            if self._cancelled:
                break
            runnable = OcrRunnable(idx, rendered_pages[idx], ocr_manager)
            runnable.signals.page_done.connect(on_page_done)
            runnable.signals.page_error.connect(on_page_error)
            self.pool.start(runnable)

        # 等待完成
        self.pool.waitForDone()

        return results
