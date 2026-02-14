# -*- mode: python ; coding: utf-8 -*-
"""
Novel Reader - PyInstaller 配置文件

使用方式:
    pyinstaller novel_reader.spec
"""

import sys
from pathlib import Path

# PySide6 需要的特殊处理
from PyInstaller.utils.hooks import qt

block_cipher = None

# 收集所有必要的导入
hiddenimports = [
    # PySide6
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtMultimedia',

    # 项目模块
    'novel_reader',
    'novel_reader.gui',
    'novel_reader.gui.pyside_main',
    'novel_reader.core',
    'novel_reader.models',

    # TTS 相关
    'piper_tts',
    'piper_tts.piper',
    'edge_tts',
    # 'torch',  # g2pW 依赖 torch，但已通过 excludes 优化

    # NLP 工具
    'g2pw',
    'g2pw.api',
    'sentence_stream',
    'unicode_rbnf',

    # 文本处理
    'jieba',
    'pypinyin',

    # 其他依赖
    'requests',
    'pathvalidate',
    'ebooklib',
    'mobi',
    'bs4',
    'lxml',
    'lxml._elementpath',
]

# 数据文件
datas = [
    # g2pW 数据文件
    ('g2pW', 'g2pW'),

    # 如果有其他需要的数据文件，在这里添加
    # ('data/*.json', 'data'),
]

# 二进制文件
binaries = []

# 分析主程序
a = Analysis(
    ['novel_reader/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'pytest',
        'tkinter',
        # AI/ML 模块（g2pW 不需要）
        'transformers',
        'tokenizers',
        'huggingface_hub',
        # CUDA/GPU 相关（不需要 GPU 加速）
        'nvidia',
        'nvidia.cuda_nvrtc',
        'nvidia.cuda_runtime',
        'nvidia.cublas',
        'nvidia.cudnn',
        'nvidia.cufft',
        'nvidia.curand',
        'nvidia.cusolver',
        'nvidia.cusparse',
        'nvidia.nccl',
        'nvidia.nvjitlink',
        'nvidia.nvshmem',
        'nvidia.cusparselt',
        'torch.cuda',
        'torch._C._cuda',
        # TensorBoard
        'tensorboard',
        'torch.utils.tensorboard',
        # Triton (GPU 编译器)
        'triton',
        'triton._C',
        'triton.language',
        'triton.compiler',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤不需要的文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='novel-reader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='novel-reader',
)
