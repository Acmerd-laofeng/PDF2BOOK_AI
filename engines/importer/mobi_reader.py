# -*- coding: utf-8 -*-
"""MOBI 读取器 — 解析 MOBI 为 ParsedDocument

v4.0.5 改进：
- 修复段落重复提取（find_all(['p','div']) → 先 p 再 div 回退）
- 合并连续行为段落
- 章节分章正则列表语法修复
"""
import os
import re
from typing import List

from engines.reader_base import BaseReader
from engines.document import ParsedDocument, Chapter

# 句末标点
_SENTENCE_END = '。！？…」』）)]}】!?;；'


class MOBIReader(BaseReader):
    """MOBI 文件解析器"""

    def read(self, file_path: str) -> ParsedDocument:
        doc = ParsedDocument(
            title=os.path.splitext(os.path.basename(file_path))[0],
            source_format="mobi",
            source_path=file_path,
        )

        try:
            from ebooklib import epub, ITEM_DOCUMENT
            from bs4 import BeautifulSoup

            book = epub.read_epub(file_path)

            if book.get_metadata("DC", "title"):
                doc.title = book.get_metadata("DC", "title")[0][0]
            if book.get_metadata("DC", "creator"):
                doc.author = book.get_metadata("DC", "creator")[0][0]

            for item in book.get_items_of_type(ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_content(), "html.parser")
                chapter_title = ""
                for tag_name in ["h1", "h2", "h3"]:
                    tag = soup.find(tag_name)
                    if tag:
                        chapter_title = tag.get_text(strip=True)
                        break

                # 修复：先 p 后 div，避免重复
                paragraphs = []
                for tag in soup.find_all("p"):
                    text = tag.get_text(strip=True)
                    if text:
                        paragraphs.append(text)
                if not paragraphs:
                    for tag in soup.find_all("div"):
                        text = tag.get_text(strip=True)
                        if text:
                            paragraphs.append(text)

                if paragraphs:
                    doc.add_chapter(
                        title=chapter_title or f"章节 {len(doc.chapters) + 1}",
                        paragraphs=paragraphs,
                    )

        except Exception:
            # MOBI 直接解析失败，尝试用 mobi 库
            try:
                import mobi
                tempdir, filepath = mobi.extract(file_path)
                if filepath.endswith(".html"):
                    from bs4 import BeautifulSoup
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")

                    all_text = []
                    for tag in soup.find_all(["p", "div", "br"]):
                        text = tag.get_text(strip=True)
                        if text:
                            all_text.append(text)

                    # 合并连续行
                    merged = self._merge_lines(all_text)

                    # 简单分章
                    chapter_patterns = [
                        r"^第[一二三四五六七八九十百千零〇\d]+[章回节].*",
                        r"^Chapter\s+\d+.*",
                    ]
                    compiled = [re.compile(p) for p in chapter_patterns]
                    current = Chapter(title="正文")
                    doc.chapters.append(current)
                    for line in merged:
                        if any(p.match(line) for p in compiled) and len(line) < 50:
                            current = Chapter(title=line)
                            doc.chapters.append(current)
                        else:
                            current.paragraphs.append(line)

                import shutil
                shutil.rmtree(tempdir, ignore_errors=True)

            except ImportError:
                raise ValueError(
                    "MOBI 解析需要安装 mobi 库：pip install mobi\n"
                    "或使用 ebooklib（对部分 MOBI 文件兼容）"
                )

        if not doc.chapters:
            doc.add_chapter(title="正文", paragraphs=[])

        doc.compute_stats()
        return doc

    @staticmethod
    def _merge_lines(lines: List[str]) -> List[str]:
        """合并连续行为段落"""
        if not lines:
            return []
        result = []
        current = lines[0]
        for i in range(1, len(lines)):
            if current and current[-1] in _SENTENCE_END:
                result.append(current)
                current = lines[i]
            else:
                current += lines[i]
        if current:
            result.append(current)
        return result
