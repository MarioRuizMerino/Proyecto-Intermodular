# -*- mode: python ; coding: utf-8 -*-
# Spec file cross-platform para MoodleAndalucia.
# Funciona en Windows y Linux sin rutas hardcodeadas.

import sys
import os
from pathlib import Path
import customtkinter

# Ruta dinámica a customtkinter (funciona en cualquier entorno/OS)
ctk_path = str(Path(customtkinter.__file__).parent)

SPEC_DIR = Path(SPECPATH)
ROOT     = SPEC_DIR.parent

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'src'), 'src'),
        (ctk_path, 'customtkinter'),
    ],
    hiddenimports=[
        # Selenium
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        # WebDriver Manager (descarga chromedriver en runtime)
        'webdriver_manager',
        'webdriver_manager.chrome',
        'webdriver_manager.core',
        'webdriver_manager.core.driver_cache',
        'webdriver_manager.core.config',
        # BeautifulSoup
        'bs4',
        'bs4.builder',
        'bs4.builder._html5lib',
        'bs4.builder._htmlparser',
        'bs4.builder._lxml',
        # Packaging
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
        # Tkinter / CustomTkinter
        'tkinter',
        'tkinter.ttk',
        '_tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MoodleAndalucia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Sin consola en Windows; en Linux se muestra para ver errores si los hay
    console=False if sys.platform.startswith('win') else False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
