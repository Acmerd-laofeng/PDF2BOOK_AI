# -*- mode: python ; coding: utf-8 -*-
"""PDF2BOOK AI - PyInstaller 打包配置（精简版）
去掉 collect_all('PySide6')，依赖 PyInstaller 内置 hook 自动处理。
"""
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = []
binaries = []
hiddenimports = []

# RapidOCR 数据文件
r1, r2, r3 = collect_all('rapidocr_onnxruntime')
datas += r1; binaries += r2; hiddenimports += r3

# ebooklib 模板文件
r1, r2, r3 = collect_all('ebooklib')
datas += r1; binaries += r2; hiddenimports += r3

# beautifulsoup4
r1, r2, r3 = collect_all('bs4')
datas += r1; binaries += r2; hiddenimports += r3

# lxml
hiddenimports += ['lxml._elementpath', 'lxml.etree']

# PySide6 — 不用 collect_all（会收集 220MB+ 无用文件导致 OOM）
# PyInstaller 内置 hook-PySide6.* 会自动收集必要的 DLL 和插件
# 只需声明 hiddenimports 确保模块被导入
hiddenimports += [
    'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
    'PySide6.QtNetwork', 'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
    'shiboken6',
]

# QFluentWidgets
r1, r2, r3 = collect_all('qfluentwidgets')
datas += r1; binaries += r2; hiddenimports += r3

# 项目资源文件
datas += [
    ('ui/theme', 'ui/theme'),
    ('resources', 'resources'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'PIL.ImageTk',
        # torch 全家桶（rapidocr 用 onnxruntime，不需要 torch CUDA）
        'torch', 'torchvision', 'torchaudio', 'torch._C',
        # paddle / jax 不是 rapidocr 的必需依赖
        'paddle', 'paddlepaddle', 'jax', 'jaxlib',
        # cv2 / opencv 82MB，rapidocr 用 PIL 处理图片
        'cv2', 'opencv',
        # imageio_ffmpeg 84MB，不需要
        'imageio_ffmpeg',
        # pyarrow 44MB，数据处理库不需要
        'pyarrow',
        # psycopg2 PostgreSQL 驱动不需要
        'psycopg2',
        # Pythonwin/MFC 不需要
        'Pythonwin', 'win32ui', 'win32uiole',
        # PIL AVIF 插件 7.5MB，PDF 不用
        'PIL._avif',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDF2BOOK_AI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)
