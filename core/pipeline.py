# -*- coding: utf-8 -*-
"""转换流水线总控

PDF → 分析 → OCR → 版面分析 → 段落重建 → 章节识别 → AI纠错 → EPUB 生成

支持逐页缓存，中断后可恢复。
每个阶段通过 EventBus 发送进度信号。
"""
import time
from pathlib import Path
from typing import Optional

from core.models import Task, ConvertSettings
from core.event_bus import event_bus
from core.cache import PageCache
from engines.pdf.analyzer import PDFAnalyzer
from engines.pdf.reader import PDFReader
from engines.pdf.renderer import Renderer
from engines.pdf.image_extractor import ImageExtractor
from engines.ocr.manager import OCRManager
from engines.layout.bbox_parser import BBoxParser
from engines.layout.paragraph_detector import ParagraphDetector
from engines.layout.chapter_detector import ChapterDetector
from engines.export.epub import EPUBBuilder
from engines.ai.corrector import Corrector


class Pipeline:
    """转换流水线

    PDF → 分析 → OCR → 版面分析 → 段落重建 → 章节识别 → AI纠错 → EPUB 生成

    支持逐页缓存，中断后可恢复。
    """

    def __init__(self):
        self.pdf_analyzer = PDFAnalyzer()
        self.pdf_reader = None
        self.renderer = Renderer()
        self.ocr = OCRManager()
        self.bbox_parser = BBoxParser()
        self.paragraph_detector = ParagraphDetector()
        self.chapter_detector = ChapterDetector()
        self.epub_builder = EPUBBuilder()
        self.page_cache = PageCache()
        self.corrector = Corrector()
        self.image_extractor = ImageExtractor()
        self._cancelled = False

        # 加载纠错字典
        dict_path = Path(__file__).parent.parent / "resources" / "dictionaries" / "ocr_corrections.json"
        if dict_path.exists():
            self.corrector.load_dictionary(str(dict_path))

    def cancel(self):
        """请求取消"""
        self._cancelled = True

    def run(self, task: Task) -> dict:
        """执行完整转换流程

        Args:
            task: 转换任务对象

        Returns:
            转换报告 dict
        """
        self._cancelled = False
        if isinstance(task.settings, ConvertSettings):
            settings = task.settings
        elif task.settings:
            settings = ConvertSettings(**task.settings)
        else:
            settings = ConvertSettings()

        # 根据质量模式自动调整 DPI
        quality_dpi_map = {
            "quick": 150,
            "standard": 300,
            "precise": 400,
            "ai": 300,
        }
        if settings.quality in quality_dpi_map:
            settings.dpi = quality_dpi_map[settings.quality]
            if settings.quality == "ai":
                settings.enable_ai_correct = True

        # 提取导出目录（ConvertSettings 没有此字段，从 task.settings dict 中取）
        settings_output_dir = ""
        if isinstance(task.settings, dict):
            settings_output_dir = task.settings.get("output_dir", "")
        elif hasattr(task.settings, 'output_dir'):
            settings_output_dir = task.settings.output_dir or ""

        start_time = time.time()

        # 日志辅助
        def log(msg: str):
            event_bus.log_message.emit(f"[Pipeline] {msg}")

        try:
            # === 阶段 1: PDF 分析 ===
            log("开始分析 PDF...")
            event_bus.task_status_changed.emit(task.id, "analyzing")
            info = self.pdf_analyzer.analyze(task.pdf_path)
            task.total_pages = info["pages"]
            event_bus.analysis_done.emit(info)
            log(f"PDF: {info['pages']} 页, 类型: {info['type']}, 预计: {info['estimated_time']}")

            # 更新段落检测参数
            self.paragraph_detector.configure(
                indent_threshold=settings.indent_threshold,
                detect_chapters=settings.detect_chapters,
                merge_cross_page=settings.merge_cross_page,
            )

            # 计算 PDF 哈希用于缓存
            pdf_hash = self.page_cache.compute_pdf_hash(task.pdf_path)

            # === 阶段 2: 逐页 OCR + 段落检测 ===
            log("开始 OCR 识别...")
            event_bus.task_status_changed.emit(task.id, "ocr")
            self.pdf_reader = PDFReader(task.pdf_path)

            all_paragraphs = []
            dpi = settings.dpi
            cached_count = 0
            total_confidence = 0.0
            ocr_page_count = 0

            total_pages = self.pdf_reader.count()

            for i in range(total_pages):
                if self._cancelled:
                    self.pdf_reader.close()
                    event_bus.task_status_changed.emit(task.id, "cancelled")
                    return {}

                # 检查缓存
                cached_blocks = self.page_cache.get(i + 1, pdf_hash)
                if cached_blocks is not None:
                    page_paragraphs = self.paragraph_detector.detect(cached_blocks, page_num=i + 1)
                    all_paragraphs.extend(page_paragraphs)
                    cached_count += 1
                    # 统计置信度
                    page_conf = sum(b.confidence for b in cached_blocks) / max(len(cached_blocks), 1)
                    total_confidence += page_conf
                    ocr_page_count += 1
                else:
                    # 渲染页面
                    page = self.pdf_reader.get_page(i)
                    pix = self.renderer.render(page, dpi=dpi)
                    img_bytes = pix.tobytes("png")

                    # OCR
                    ocr_result = self.ocr.run(img_bytes)

                    # 统计置信度
                    if ocr_result:
                        page_conf = sum(b.confidence for b in ocr_result) / len(ocr_result)
                        total_confidence += page_conf
                        ocr_page_count += 1

                    # 保存缓存
                    self.page_cache.save(i + 1, ocr_result, pdf_hash)

                    # 段落检测
                    page_paragraphs = self.paragraph_detector.detect(ocr_result, page_num=i + 1)
                    all_paragraphs.extend(page_paragraphs)

                # 更新进度 (10% - 80%)
                progress = 10 + int((i + 1) / total_pages * 70)
                event_bus.progress.emit(task.filename, progress)
                task.current_page = i + 1

                if (i + 1) % 10 == 0 or i == total_pages - 1:
                    log(f"OCR 进度: {i + 1}/{total_pages} 页")

            self.pdf_reader.close()
            log(f"OCR 完成, 缓存命中 {cached_count} 页")

            if not all_paragraphs:
                raise ValueError("未从 PDF 中识别到任何文字")

            # === 阶段 3: 后处理（跨页合并 + 噪音过滤）===
            log("开始排版整理...")
            event_bus.task_status_changed.emit(task.id, "exporting")  # 后处理归入导出阶段
            all_paragraphs = self.paragraph_detector.postprocess(all_paragraphs)
            log(f"排版完成: {len(all_paragraphs)} 段落")

            # === 阶段 3b: 章节检测 ===
            if settings.detect_chapters:
                log("开始章节识别...")
                all_paragraphs = self.chapter_detector.detect_and_mark(all_paragraphs)
                chapter_list = self.chapter_detector.extract_chapters(all_paragraphs)
                log(f"识别到 {len(chapter_list)} 个章节")
            else:
                chapter_list = []

            # === 阶段 3c: OCR 纠错 ===
            correction_count = 0
            correction_report = {}
            if self.corrector.dictionary_size > 0:
                log("开始 OCR 纠错...")
                all_paragraphs = self.corrector.correct_paragraphs(all_paragraphs)
                correction_count = self.corrector.total_corrections
                log(f"本地字典纠错完成: {correction_count} 处修正")

                # 生成纠错报告
                correction_report = self.corrector.generate_correction_report(all_paragraphs)
                if correction_report["total_findings"] > 0:
                    log(f"潜在错误: {correction_report['total_findings']} 处")

            # === 阶段 3c-2: AI 纠错（Gemini）===
            if settings.enable_ai_correct:
                from app.config import Config
                provider = Config.get_ai_provider()
                api_key = Config.get_ai_api_key()
                ai_model = Config.get_ai_model()

                if provider == "gemini" and api_key:
                    from engines.ai.llm_client import LLMClient
                    llm = LLMClient(api_key=api_key, model=ai_model)
                    log(f"启用 Gemini AI 纠错（模型: {ai_model}）...")
                    all_paragraphs = self.corrector.llm_correct(all_paragraphs, llm)
                    if llm.last_error and llm.call_count == 0:
                        log(f"AI 纠错失败: {llm.last_error}")
                    # 更新纠错报告
                    correction_report = self.corrector.generate_correction_report(all_paragraphs)
                else:
                    log("AI 纠错已启用但未配置 API Key，跳过")

            total_chars = sum(len(p[1]) for p in all_paragraphs)

            # === 阶段 3d: 图片提取 ===
            extracted_images = []
            if settings.enable_image_extract:
                log("开始提取图片...")
                try:
                    self.pdf_reader = PDFReader(task.pdf_path)
                    doc = self.pdf_reader.doc
                    for i in range(min(total_pages, doc.page_count)):
                        page_imgs = self.image_extractor.extract_from_page(doc, i)
                        extracted_images.extend(page_imgs)
                    self.pdf_reader.close()
                    log(f"提取到 {len(extracted_images)} 张图片")
                except Exception as e:
                    log(f"图片提取失败（不影响正文）: {e}")
                    extracted_images = []

            # === 阶段 4: EPUB 生成 ===
            log("开始生成 EPUB...")
            event_bus.task_status_changed.emit(task.id, "exporting")
            event_bus.progress.emit(task.filename, 92)

            book_title = task.filename.rsplit(".", 1)[0]

            # 导出路径优先级：task.output_path > settings.output_dir > PDF 同级目录
            if task.output_path:
                epub_path = task.output_path
            elif settings_output_dir:
                epub_path = str(Path(settings_output_dir) / f"{book_title}.epub")
            else:
                # 默认导出到 PDF 同级目录
                pdf_parent = Path(task.pdf_path).parent
                epub_path = str(pdf_parent / f"{book_title}.epub")

            # 确保输出目录存在
            output_dir = Path(epub_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # 获取资源目录
            resources_dir = Path(__file__).parent.parent / "resources"
            epub_themes_dir = resources_dir / "epub_themes"

            epub_stats = self.epub_builder.build(
                paragraphs=all_paragraphs,
                title=book_title,
                author=info.get("author", "Unknown") if info else "Unknown",
                output_path=epub_path,
                theme=settings.epub_theme,
                theme_dir=str(epub_themes_dir) if epub_themes_dir.exists() else None,
                images=extracted_images if extracted_images else None,
            )
            log(f"EPUB 生成: {epub_path}")

            # === 完成 ===
            elapsed = time.time() - start_time
            avg_confidence = (total_confidence / ocr_page_count * 100) if ocr_page_count > 0 else 0

            event_bus.progress.emit(task.filename, 100)
            event_bus.task_status_changed.emit(task.id, "completed")
            event_bus.log_message.emit(
                f"转换完成: {book_title} | "
                f"{task.total_pages} 页 → {epub_stats['chapter_count']} 章 | "
                f"{epub_stats['total_paragraphs']} 段, {total_chars} 字 | "
                f"耗时 {self._format_duration(elapsed)}"
            )

            task.output_path = epub_path
            task.progress = 100

            # 缓存恢复信息
            resume_info = self.page_cache.get_resume_info(total_pages, pdf_hash)

            # 返回转换报告
            return {
                "filename": task.filename,
                "author": info.get("author", "Unknown") if info else "Unknown",
                "total_pages": task.total_pages,
                "total_paragraphs": epub_stats["total_paragraphs"],
                "total_chars": total_chars,
                "chapters": epub_stats["chapter_count"],
                "chapter_titles": epub_stats["chapter_titles"],
                "images": len(extracted_images),
                "errors": 0,
                "corrections": correction_count,
                "correction_report": correction_report,
                "accuracy": round(avg_confidence, 1),
                "duration": self._format_duration(elapsed),
                "output_path": epub_path,
                "output_size": epub_stats["file_size"],
                "cached_pages": cached_count,
                "heading_count": epub_stats["heading_count"],
                "body_count": epub_stats["body_count"],
                "resume_info": resume_info,
                "pdf_hash": pdf_hash,
            }

        except Exception as e:
            event_bus.task_status_changed.emit(task.id, "error")
            event_bus.error.emit(task.filename, str(e))
            event_bus.log_message.emit(f"[Pipeline] 错误: {e}")
            task.error = str(e)
            task.status = "error"
            raise

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.0f} 秒"
        elif seconds < 3600:
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m} 分 {s} 秒"
        else:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            return f"{h} 小时 {m} 分"
