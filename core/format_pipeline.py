# -*- coding: utf-8 -*-
"""格式转换 Pipeline — 读取 → 解析 → 导出

独立于 OCR Pipeline，不依赖 TaskManager 的状态机。
但通过 EventBus 广播进度和完成事件，复用现有 UI 反馈机制。
"""
import os
from typing import Optional

from engines.importer import read_document
from engines.exporters import export_document
from engines.document import ParsedDocument
from core.event_bus import event_bus
from app.format_constants import DEFAULT_EXPORT_OPTIONS


class FormatPipeline:
    """格式转换流水线

    流程：
    1. 读取源文件 → ParsedDocument
    2. 导出为目标格式
    3. 广播进度和完成事件
    """

    def __init__(self):
        self._cancelled = False

    def run(self, source_path: str, target_format: str,
            output_path: str = "",
            options: dict = None) -> dict:
        """执行格式转换

        Args:
            source_path: 源文件路径
            target_format: 目标格式 (pdf/epub/txt/mobi)
            output_path: 输出路径（空则自动生成）
            options: 导出选项

        Returns:
            报告字典
        """
        filename = os.path.basename(source_path)
        basename = os.path.splitext(filename)[0]

        # 自动生成输出路径
        if not output_path:
            output_path = str(
                os.path.join(
                    os.path.dirname(source_path),
                    f"{basename}.{target_format}"
                )
            )

        # 合并默认选项
        if options is None:
            options = {}
        default_opts = DEFAULT_EXPORT_OPTIONS.get(target_format, {}).copy()
        default_opts.update(options)
        options = default_opts

        event_bus.log_message.emit(f"开始格式转换: {filename} → {target_format.upper()}")

        # 阶段 1：读取（20%）
        event_bus.progress.emit(filename, 10)
        if self._cancelled:
            return {}

        try:
            doc = read_document(source_path)
        except Exception as e:
            event_bus.error.emit(filename, f"读取失败: {e}")
            raise

        event_bus.progress.emit(filename, 20)
        event_bus.log_message.emit(
            f"读取完成: {doc.chapter_count} 章, {doc.total_chars} 字"
        )

        if self._cancelled:
            return {}

        # 阶段 2：导出（20% → 90%）
        event_bus.progress.emit(filename, 30)

        try:
            actual_path = export_document(doc, output_path, target_format, options)
        except Exception as e:
            event_bus.error.emit(filename, f"导出失败: {e}")
            raise

        event_bus.progress.emit(filename, 90)

        # 阶段 3：完成（100%）
        event_bus.progress.emit(filename, 100)

        report = {
            "filename": filename,
            "output_path": actual_path,
            "source_format": doc.source_format,
            "target_format": target_format,
            "title": doc.title,
            "author": doc.author,
            "chapters": doc.chapter_count,
            "total_chars": doc.total_chars,
            "total_pages": 0,  # 格式转换不涉及页数
            "is_format_convert": True,
        }

        event_bus.report_ready.emit(report)
        event_bus.finished.emit(filename)
        event_bus.log_message.emit(
            f"格式转换完成: {filename} → {target_format.upper()} "
            f"({doc.chapter_count} 章, {doc.total_chars} 字)"
        )

        self._last_report = report

        return report

    def cancel(self):
        """请求取消"""
        self._cancelled = True
