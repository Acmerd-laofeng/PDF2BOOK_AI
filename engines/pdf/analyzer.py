# -*- coding: utf-8 -*-
"""PDF 智能分析器"""
import os
import fitz
from typing import Dict


class PDFAnalyzer:
    """PDF 智能检测

    自动检测：
    - 是否有文字层
    - 是否为扫描版
    - 页数
    - 图片比例
    - 页面尺寸
    - 是否有目录
    - 预计耗时
    """

    def analyze(self, pdf_path: str) -> Dict:
        """分析 PDF

        Returns:
            {
                "pages": int,
                "type": "text" | "scan" | "mixed",
                "text_pages": int,
                "image_pages": int,
                "page_size": [w, h],
                "file_size": int,
                "has_toc": bool,
                "toc": list,
                "estimated_time": str,
            }
        """
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        text_pages = 0
        image_pages = 0
        sample_size = min(total_pages, 20)  # 采样前 20 页

        for i in range(sample_size):
            page = doc[i]
            text = page.get_text().strip()
            images = page.get_images()

            if len(text) > 50:
                text_pages += 1
            elif images:
                image_pages += 1

        # 获取页面尺寸（只需打开一次）
        page_size = [doc[0].rect.width, doc[0].rect.height] if total_pages > 0 else [0, 0]
        toc = doc.get_toc()
        has_toc = len(toc) > 0
        file_size = os.path.getsize(pdf_path)

        # 元数据
        meta = doc.metadata or {}
        author = meta.get("author", "") or ""
        doc.close()

        # 判断类型
        if sample_size > 0:
            text_ratio = text_pages / sample_size
            if text_ratio > 0.7:
                pdf_type = "text"
            elif text_ratio < 0.3:
                pdf_type = "scan"
            else:
                pdf_type = "mixed"
        else:
            pdf_type = "unknown"

        # 估算页数（按采样比例推算）
        est_text_pages = int(text_pages * total_pages / max(sample_size, 1))
        est_image_pages = int(image_pages * total_pages / max(sample_size, 1))

        # 预计耗时（基于 300 DPI 经验值：每页约 4-6 秒）
        est_seconds = total_pages * 5
        if est_seconds < 60:
            est_time = f"约 {est_seconds} 秒"
        elif est_seconds < 3600:
            est_time = f"约 {est_seconds // 60} 分钟"
        else:
            est_time = f"约 {est_seconds / 3600:.1f} 小时"

        return {
            "pages": total_pages,
            "type": pdf_type,
            "text_pages": est_text_pages,
            "image_pages": est_image_pages,
            "page_size": page_size,
            "file_size": file_size,
            "has_toc": has_toc,
            "toc": toc,
            "estimated_time": est_time,
            "author": author,
        }
