"""
PyInstaller hook for auto_thanks package.

This hook ensures all necessary data files and hidden imports
are included in the bundled executable.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all submodules
hiddenimports = collect_submodules('auto_thanks')

# Collect data files (templates, etc.)
datas = collect_data_files('auto_thanks')
