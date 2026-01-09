# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Auto Thanks Clicker.

This configuration creates a single executable file that includes:
- All Python source code from src/auto_thanks/
- Template images from templates/
- Default configuration file

Usage:
    pyinstaller auto_thanks.spec

Requirements: 7.1
"""

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = os.path.dirname(os.path.abspath(SPEC))

# Analysis configuration
a = Analysis(
    # Entry point script
    [os.path.join(project_root, 'src', 'auto_thanks', 'main.py')],
    
    # Additional paths to search for imports
    pathex=[
        os.path.join(project_root, 'src'),
    ],
    
    # Binary files to include (DLLs, etc.)
    binaries=[],
    
    # Data files to include (templates, config, etc.)
    datas=[
        # Include templates directory
        (os.path.join(project_root, 'templates'), 'templates'),
    ] + (
        # Include default config if exists
        [(os.path.join(project_root, 'config.json'), '.')]
        if os.path.exists(os.path.join(project_root, 'config.json'))
        else []
    ),
    
    # Hidden imports that PyInstaller might miss
    hiddenimports=[
        # pystray backends
        'pystray._win32',
        # PIL/Pillow modules
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageDraw',
        # tkinter for settings window
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        # APScheduler components
        'apscheduler.schedulers.background',
        'apscheduler.triggers.interval',
        'apscheduler.executors.pool',
        # OpenCV
        'cv2',
        # numpy (required by OpenCV)
        'numpy',
        # pyautogui
        'pyautogui',
        'pyscreeze',
        'pytweening',
        'mouseinfo',
        # pywin32
        'win32api',
        'win32con',
        'win32gui',
        'win32ui',
        'win32process',
        # Standard library
        'json',
        'logging',
        'threading',
        'dataclasses',
        'datetime',
        'typing',
        'pathlib',
        'time',
        'ctypes',
    ],
    
    # Modules to exclude (reduce size)
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'hypothesis',
        'pytest_cov',
        '_pytest',
    ],
    
    # Hook directories for custom hooks
    hookspath=[
        os.path.join(project_root, 'hooks'),
    ],
    
    # Runtime hooks
    runtime_hooks=[],
    
    # Don't use UPX compression (can cause issues)
    noarchive=False,
    
    # Optimize bytecode
    optimize=0,
)

# PYZ archive (compressed Python modules)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    
    # Output filename
    name='AutoThanksClicker',
    
    # Debug mode (set to False for release)
    debug=False,
    
    # Boot loader ignore signals
    bootloader_ignore_signals=False,
    
    # Strip symbols (reduce size)
    strip=False,
    
    # UPX compression (disabled for stability)
    upx=False,
    upx_exclude=[],
    
    # Runtime temp directory name
    runtime_tmpdir=None,
    
    # Console window (False = GUI app, no console)
    console=False,
    
    # Disable windowed mode traceback
    disable_windowed_traceback=False,
    
    # Argv emulation (macOS only)
    argv_emulation=False,
    
    # Target architecture
    target_arch=None,
    
    # Code signing (None = no signing)
    codesign_identity=None,
    entitlements_file=None,
    
    # Icon file (optional - can be added later)
    # icon='icon.ico',
    
    # Version info (Windows only)
    version=None,
    
    # UAC manifest (Windows only)
    uac_admin=False,
    uac_uiaccess=False,
)
