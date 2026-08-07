# -*- coding: utf-8 -*-
"""EPUB 生成器 - 从 v2 迁移 + 主题支持 + 增强分章

功能：
- 按章节标题分章
- 每章独立 xhtml 文件
- CSS 主题切换（外部文件优先）
- 目录（TOC + NCX）
- HTML 转义处理
- 无标题时按页数分章
- 返回生成统计信息
"""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict

from ebooklib import epub


class EPUBBuilder:
    """EPUB 生成器"""

    # 内置 CSS 主题（外部文件不存在时回退）
    THEMES = {
        "classic": """
body { font-family: serif; line-height: 1.8; margin: 5%; }
p { text-indent: 2em; margin: 0.5em 0; }
h1 { text-align: center; font-size: 1.6em; margin: 1.5em 0 0.5em; }
h2 { text-align: center; font-size: 1.3em; margin: 1.2em 0 0.5em; color: #333; }
h3 { font-size: 1.1em; margin: 1em 0 0.3em; }
.figure { text-align: center; margin: 1em 0; page-break-inside: avoid; }
.figure img { max-width: 100%; height: auto; }
""",
        "kindle": """
body { font-family: serif; line-height: 1.6; margin: 3%; }
p { text-indent: 2em; margin: 0.3em 0; }
h1 { text-align: center; font-size: 1.5em; margin: 1em 0 0.5em; }
h2 { text-align: center; font-size: 1.2em; margin: 1em 0 0.5em; }
h3 { font-size: 1.1em; margin: 0.8em 0 0.3em; }
.figure { text-align: center; margin: 0.8em 0; page-break-inside: avoid; }
.figure img { max-width: 100%; height: auto; }
""",
        "modern": """
body { font-family: sans-serif; line-height: 1.8; margin: 8%; }
p { text-indent: 2em; margin: 0.6em 0; }
h1 { text-align: center; font-size: 1.8em; margin: 2em 0 0.8em; color: #1a73e8; }
h2 { text-align: center; font-size: 1.4em; margin: 1.5em 0 0.6em; color: #333; }
h3 { font-size: 1.1em; margin: 1em 0 0.4em; color: #555; }
.figure { text-align: center; margin: 1.5em 0; page-break-inside: avoid; }
.figure img { max-width: 100%; height: auto; border-radius: 4px; }
""",
        "eye_care": """
body { font-family: serif; line-height: 2.0; margin: 6%; background: #f5f0e8; color: #3a3a3a; }
p { text-indent: 2em; margin: 0.5em 0; }
h1 { text-align: center; font-size: 1.6em; margin: 1.5em 0 0.5em; color: #5a4a3a; }
h2 { text-align: center; font-size: 1.3em; margin: 1.2em 0 0.5em; color: #6a5a4a; }
h3 { font-size: 1.1em; margin: 1em 0 0.3em; color: #6a5a4a; }
.figure { text-align: center; margin: 1.2em 0; page-break-inside: avoid; }
.figure img { max-width: 100%; height: auto; opacity: 0.95; }
""",
    }

    def build(self, paragraphs: List[Tuple[str, str]],
              title: str, author: str, output_path: str,
              theme: str = "classic",
              theme_dir: Optional[str] = None,
              images: Optional[List[Dict]] = None) -> Dict:
        """生成 EPUB

        Args:
            paragraphs: 段落列表 [(type, text), ...]  type: 'heading' | 'body'
            title: 书名
            author: 作者
            output_path: 输出路径
            theme: CSS 主题名
            theme_dir: 外部主题目录
            images: 图片列表 [{image_bytes, ext, page, index}, ...]

        Returns:
            生成统计信息 dict
        """
        book = epub.EpubBook()
        book.set_identifier(f"pdf2book-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        book.set_title(title)
        book.add_author(author)
        book.set_language("zh-CN")

        # CSS 主题：优先从外部文件加载
        css_content = self._load_theme_css(theme, theme_dir)
        css = epub.EpubItem(
            uid="style",
            file_name="style/default.css",
            media_type="text/css",
            content=css_content.encode("utf-8"),
        )
        book.add_item(css)

        # 初始化 spine 和章节列表
        spine = ["nav"]
        epub_chapters = []
        chapter_titles = []

        # 添加图片（如果有）
        image_count = 0
        if images:
            for img in images:
                img_uid = f"img_p{img['page']}_i{img['index']}"
                img_filename = f"images/{img_uid}.{img['ext']}"
                img_item = epub.EpubItem(
                    uid=img_uid,
                    file_name=img_filename,
                    media_type=f"image/{img['ext']}",
                    content=img["image_bytes"],
                )
                book.add_item(img_item)
                image_count += 1

            # 在 spine 中添加图片展示页（所有图片集中在一页）
            if image_count > 0:
                img_html_parts = [
                    '<?xml version="1.0" encoding="utf-8"?>',
                    '<!DOCTYPE html>',
                    '<html xmlns="http://www.w3.org/1999/xhtml">',
                    '<head>',
                    '<title>图片附录</title>',
                    '<link rel="stylesheet" type="text/css" href="style/default.css"/>',
                    '</head>',
                    '<body>',
                    f'<h2>图片附录</h2>',
                ]
                for img in images:
                    img_uid = f"img_p{img['page']}_i{img['index']}"
                    img_filename = f"images/{img_uid}.{img['ext']}"
                    img_html_parts.append(
                        f'<div class="figure"><img src="{img_filename}" alt="第{img["page"]+1}页图片"/></div>'
                    )
                img_html_parts.extend(['</body>', '</html>'])
                img_chapter = epub.EpubHtml(
                    title="图片附录",
                    file_name="images_appendix.xhtml",
                    content="\n".join(img_html_parts).encode("utf-8"),
                )
                img_chapter.add_item(css)
                book.add_item(img_chapter)
                spine.append(img_chapter)
                epub_chapters.append(img_chapter)
                chapter_titles.append("图片附录")

        # 按标题分章
        chapters_raw = self._split_chapters(paragraphs)

        # 如果没有标题分隔，按 50 段分章
        if not chapters_raw:
            chapters_raw = self._split_by_size(paragraphs, chunk_size=50)

        if not chapters_raw:
            chapters_raw = [paragraphs]

        # 如果第一章没有标题，加书名标题
        if chapters_raw and chapters_raw[0] and chapters_raw[0][0][0] != 'heading':
            chapters_raw[0].insert(0, ('heading', title))

        for ci, chap_paras in enumerate(chapters_raw):
            chap_title = "未知章节"
            for p_type, p_text in chap_paras:
                if p_type == 'heading':
                    chap_title = p_text
                    break
            else:
                chap_title = f"第 {ci + 1} 节"

            chapter_titles.append(chap_title)
            file_name = f"chap_{ci + 1}.xhtml"

            html_parts = [
                '<?xml version="1.0" encoding="utf-8"?>',
                '<!DOCTYPE html>',
                '<html xmlns="http://www.w3.org/1999/xhtml">',
                '<head>',
                f'<title>{self._escape_xml(chap_title)}</title>',
                '<link rel="stylesheet" type="text/css" href="style/default.css"/>',
                '</head>',
                '<body>',
            ]

            for p_type, p_text in chap_paras:
                safe = self._escape_html(p_text)
                if p_type == 'heading':
                    if ci == 0 and p_text == chap_title:
                        html_parts.append(f'<h1>{safe}</h1>')
                    else:
                        html_parts.append(f'<h2>{safe}</h2>')
                else:
                    html_parts.append(f'<p>{safe}</p>')

            html_parts.extend(['</body>', '</html>'])
            html_content = "\n".join(html_parts)

            chapter = epub.EpubHtml(
                title=chap_title,
                file_name=file_name,
                content=html_content.encode("utf-8"),
            )
            chapter.add_item(css)
            book.add_item(chapter)
            epub_chapters.append(chapter)
            spine.append(chapter)

        # 目录
        book.toc = epub_chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = spine

        epub.write_epub(output_path, book, {})

        # 返回统计信息
        total_chars = sum(len(p[1]) for p in paragraphs)
        heading_count = sum(1 for p in paragraphs if p[0] == 'heading')
        body_count = len(paragraphs) - heading_count

        return {
            "chapter_count": len(chapters_raw),
            "chapter_titles": chapter_titles,
            "total_paragraphs": len(paragraphs),
            "heading_count": heading_count,
            "body_count": body_count,
            "total_chars": total_chars,
            "image_count": image_count,
            "output_path": output_path,
            "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
        }

    def _split_chapters(self, paragraphs: List[Tuple[str, str]]) -> List[List[Tuple[str, str]]]:
        """按标题分章

        如果没有 heading，返回空列表（由调用方处理 fallback）。
        """
        chapters = []
        current_chap = []
        has_heading = False

        for p_type, p_text in paragraphs:
            if p_type == 'heading':
                has_heading = True
                if current_chap:
                    chapters.append(current_chap)
                current_chap = [('heading', p_text)]
            else:
                current_chap.append((p_type, p_text))

        if has_heading and current_chap:
            chapters.append(current_chap)

        return chapters

    def _split_by_size(self, paragraphs: List[Tuple[str, str]],
                        chunk_size: int = 50) -> List[List[Tuple[str, str]]]:
        """无标题时按段落数分章"""
        chapters = []
        for i in range(0, len(paragraphs), chunk_size):
            chunk = paragraphs[i:i + chunk_size]
            # 为每章加一个标题
            chap_num = i // chunk_size + 1
            chunk.insert(0, ('heading', f"第 {chap_num} 节"))
            chapters.append(chunk)
        return chapters

    def _load_theme_css(self, theme: str, theme_dir: Optional[str] = None) -> str:
        """加载主题 CSS

        优先从外部文件加载（resources/epub_themes/xxx.css），
        找不到则使用内置主题。
        """
        if theme_dir:
            css_path = Path(theme_dir) / f"{theme}.css"
            if css_path.exists():
                return css_path.read_text(encoding='utf-8')

        # 回退到内置主题
        return self.THEMES.get(theme, self.THEMES["classic"])

    @staticmethod
    def _escape_html(text: str) -> str:
        """HTML 转义"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    @staticmethod
    def _escape_xml(text: str) -> str:
        """XML 转义"""
        return EPUBBuilder._escape_html(text)
