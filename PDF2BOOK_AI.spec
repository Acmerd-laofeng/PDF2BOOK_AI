# -*- mode: python ; coding: utf-8 -*-
"""PDF2BOOK AI - PyInstaller 打包配置"""
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# 收集所有动态依赖
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

# PySide6 插件
r1, r2, r3 = collect_all('PySide6')
datas += r1; binaries += r2; hiddenimports += r3

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
    excludes=['tkinter', 'matplotlib', 'scipy'],
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
    console=False,          # GUI 模式，无控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',  # 图标（需自行添加）
)
