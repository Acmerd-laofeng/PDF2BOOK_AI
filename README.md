# PDF2BOOK AI v3.0

AI 智能电子书重构平台 — 从扫描 PDF 到精美 EPUB

## 技术栈

| 模块 | 技术 |
|------|------|
| GUI | PySide6 + QFluentWidgets (Win11 Fluent Design) |
| PDF | PyMuPDF (fitz) |
| OCR | rapidocr-onnxruntime |
| EPUB | ebooklib |
| 数据库 | SQLite |
| 打包 | PyInstaller |

## 项目结构

```
PDF2BOOK_AI/
├── main.py                    # 程序入口
├── requirements.txt           # 依赖
├── PDF2BOOK_AI.spec           # PyInstaller 打包配置
├── app/                       # 应用层
│   ├── bootstrap.py           # 启动初始化
│   ├── config.py              # 全局配置
│   └── constants.py           # 常量定义
├── ui/                        # UI 层
│   ├── main_window.py         # 主窗口 (FluentWindow)
│   ├── pages/                 # 5 个页面
│   │   ├── home_page.py       # 首页 (拖拽上传)
│   │   ├── convert_page.py    # 转换中心
│   │   ├── library_page.py    # 我的书库
│   │   ├── task_page.py       # 任务中心
│   │   └── setting_page.py    # 设置中心
│   ├── widgets/               # 可复用组件
│   │   ├── pdf_drop_area.py   # PDF 拖拽区域
│   │   ├── analysis_card.py   # PDF 分析卡片
│   │   ├── task_card.py       # 任务卡片
│   │   ├── book_card.py       # 书籍卡片
│   │   ├── progress_card.py   # 进度卡片
│   │   ├── theme_card.py      # 主题选择卡片
│   │   ├── book_preview.py    # EPUB 预览
│   │   └── report_view.py     # 转换报告
│   ├── dialogs/               # 弹窗
│   │   ├── pdf_analyzer_dialog.py
│   │   └── report_dialog.py
│   └── theme/                 # QSS 主题
│       ├── dark.qss
│       └── light.qss
├── core/                      # 核心层
│   ├── pipeline.py            # 转换流水线
│   ├── converter.py           # 转换服务
│   ├── task_manager.py        # 任务管理器
│   ├── event_bus.py           # 事件总线 (Qt Signal)
│   ├── worker.py              # QThread Worker
│   └── models.py              # 数据模型
├── engines/                   # 引擎层
│   ├── pdf/                   # PDF 引擎
│   │   ├── analyzer.py        # 智能检测
│   │   ├── reader.py          # 读取封装
│   │   └── renderer.py        # 页面渲染
│   ├── ocr/                   # OCR 引擎
│   │   ├── base.py            # 抽象接口
│   │   ├── rapidocr_engine.py # RapidOCR 实现
│   │   └── manager.py         # 引擎管理器
│   ├── layout/                # 版面分析
│   │   ├── bbox_parser.py     # 坐标解析
│   │   ├── paragraph_detector.py  # 段落检测 (v2 核心算法)
│   │   ├── chapter_detector.py    # 章节识别
│   │   └── table_detector.py      # 表格检测 (v4 预留)
│   ├── ai/                    # AI 模块 (v4 预留)
│   │   ├── corrector.py       # OCR 纠错
│   │   ├── summarizer.py      # 摘要生成
│   │   └── llm_client.py      # LLM 网关
│   └── export/                # 导出引擎
│       ├── epub.py            # EPUB 生成器 (4 主题)
│       ├── mobi.py            # MOBI (v5 预留)
│       ├── html.py            # HTML (v5 预留)
│       └── markdown.py        # Markdown (v5 预留)
├── database/                  # 数据库
│   ├── db.py                  # SQLite 封装
│   └── models.py              # 数据模型
├── tests/                     # 单元测试
│   ├── test_paragraph_detector.py
│   ├── test_chapter_detector.py
│   ├── test_epub_builder.py
│   └── test_pdf_analyzer.py
├── cache/                     # 运行时缓存
│   ├── pages/
│   ├── ocr/
│   └── preview/
├── models/                    # 模型文件
│   ├── ocr/
│   ├── ai/
│   └── language/
└── resources/                 # 资源文件
    ├── templates/
    ├── epub_themes/
    └── dictionaries/
```

## 开发计划

| 版本 | 目标 | 状态 |
|------|------|------|
| v3.0 | 架构重构 + PySide6 UI + 引擎层拆分 | 🚧 骨架完成 |
| v4.0 | AI 纠错 + 章节增强 + 图片/表格 | 📋 规划中 |
| v5.0 | 书库管理 + 批量转换 + 商业化 | 📋 规划中 |

## 运行

```bash
pip install -r requirements.txt
python main.py
```

## 打包

```bash
pyinstaller PDF2BOOK_AI.spec
```
