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
        # llvmlite 102MB — numba JIT 编译，rapidocr/onnxruntime 不需要
        'llvmlite', 'numba',
        # PySide6 视频编解码 15.8MB，PDF 工具不需要
        'PySide6.QtMultimedia', 'PySide6.Qt3DCore', 'PySide6.Qt3DRender',
        'PySide6.Qt3DInput', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras',
        'PySide6.Qt3DLogic',
        # PySide6 软渲染 19.7MB，有 GPU 时不需要
        # 'PySide6.QtOpenGL',
        # 加密库 8.7MB，PDF 工具不需要
        'cryptography',
        # 数据验证 5MB，间接依赖可选
        'pydantic',
        # 几何计算 2.4MB，不需要
        'Shapely', 'shapely',
        # 其他不需要的
        'IPython', 'jupyter', 'notebook', 'jupyter_client',
        'pytest', 'setuptools', 'pip', 'wheel',
        'mkl', 'mkl_fft',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# --- 过滤不需要的二进制文件 ---
# PySide6 全局 hook 会收集所有 Qt DLL，手动排除不需要的
_strip_patterns = [
    'opengl32sw', 'opengl32',  # 软渲染 19.7MB
    'avformat-', 'avcodec-', 'avdevice-',  # 视频编解码
    'avutil-', 'swscale-', 'swresample-', 'avfilter-',
    'Qt63D', 'Qt6Quick', 'Qt6Quick3D', 'Qt6Qml',  # 3D/QML
    'Qt6WebEngine', 'Qt6WebChannel', 'Qt6WebSockets',
    'Qt6Multimedia', 'Qt6SpatialAudio',
    'Qt6Bluetooth', 'Qt6Nfc', 'Qt6SerialBus', 'Qt6SerialPort',
    'Qt6Sensors', 'Qt6Positioning', 'Qt6Location',
    'Qt6Sql', 'Qt6Test', 'Qt6Designer', 'Qt6Help',
    'Qt6Charts', 'Qt6DataVisualization', 'Qt6Graphs',
    'Qt6Pdf',  # PySide6 PDF 模块（我们有 pymupdf）
    'Qt6Scxml', 'Qt6RemoteObjects', 'Qt6NetworkAuth',
    # llvmlite
    'llvmlite',
    # debug/debugger
    'debug',
]

_filtered_binaries = []
for dest, src, kind in a.binaries:
    skip = False
    dest_lower = dest.lower()
    for pat in _strip_patterns:
        if pat.lower() in dest_lower:
            skip = True
            break
    if not skip:
        _filtered_binaries.append((dest, src, kind))
a.binaries = _filtered_binaries

# 过滤 datas 中的不需要的文件
_filtered_datas = []
for dest, src, kind in a.datas:
    dest_lower = dest.lower()
    skip = False
    for pat in ['debug', 'qmltooling', 'qt6quick', 'qt6qml', 'qt63d', 'qt6webengine', 'translations/qt']:
        if pat in dest_lower:
            skip = True
            break
    if not skip:
        _filtered_datas.append((dest, src, kind))
a.datas = _filtered_datas

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
