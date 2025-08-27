# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the source directory
src_dir = Path('src')
clusterm_dir = src_dir / 'clusterm'

# Find libz.so.1 in common locations
libz_paths = ['/lib64/libz.so.1', '/usr/lib64/libz.so.1', '/lib/x86_64-linux-gnu/libz.so.1']
libz_binaries = [(path, '.') for path in libz_paths if os.path.exists(path)]

a = Analysis(
    ['main_entry.py'],
    pathex=['src'],
    binaries=libz_binaries,
    datas=[
        # Include CSS files for textual UI styling
        (str(clusterm_dir / 'ui' / 'styles'), 'clusterm/ui/styles'),
    ],
    hiddenimports=[
        # Textual framework imports - comprehensive list
        'textual',
        'textual.app',
        'textual.widgets',
        'textual.widgets._tab_pane',
        'textual.widgets._data_table',
        'textual.widgets._button',
        'textual.widgets._static',
        'textual.widgets._label',
        'textual.widgets._header',
        'textual.widgets._footer',
        'textual.widgets._log',
        'textual.containers',
        'textual.screen',
        'textual.reactive',
        'textual.events',
        'textual.message',
        'textual.css',
        'textual.color',
        'textual.driver',
        # Prompt toolkit imports
        'prompt_toolkit',
        'prompt_toolkit.completion',
        'prompt_toolkit.shortcuts',
        'prompt_toolkit.key_binding',
        'prompt_toolkit.formatted_text',
        'prompt_toolkit.application',
        # PyYAML imports
        'yaml',
        # Other clusterm modules
        'clusterm.core',
        'clusterm.k8s',
        'clusterm.ui',
        'clusterm.plugins',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules to reduce size
        'pytest',
        'test',
        'tests',
        # Exclude development tools
        'mypy',
        'ruff',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='clusterm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)