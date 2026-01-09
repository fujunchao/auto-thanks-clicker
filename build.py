#!/usr/bin/env python
"""
Build script for Auto Thanks Clicker.

This script automates the PyInstaller build process and handles
common build tasks like cleaning, building, and verifying the output.

Usage:
    python build.py [--clean] [--verify]

Options:
    --clean     Clean build artifacts before building
    --verify    Verify the built executable exists after building
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.absolute()


def clean_build_artifacts(project_root: Path) -> None:
    """
    Clean build artifacts from previous builds.
    
    Args:
        project_root: Project root directory
    """
    print("Cleaning build artifacts...")
    
    dirs_to_clean = [
        project_root / "build",
        project_root / "dist",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"  Removing: {dir_path}")
            shutil.rmtree(dir_path)
    
    # Clean .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        pyc_file.unlink()
    
    # Clean __pycache__ directories
    for pycache_dir in project_root.rglob("__pycache__"):
        if pycache_dir.is_dir():
            shutil.rmtree(pycache_dir)
    
    print("Clean complete.")


def build_executable(project_root: Path) -> bool:
    """
    Build the executable using PyInstaller.
    
    Args:
        project_root: Project root directory
        
    Returns:
        True if build was successful, False otherwise
    """
    print("Building executable...")
    
    spec_file = project_root / "auto_thanks.spec"
    
    if not spec_file.exists():
        print(f"Error: Spec file not found: {spec_file}")
        return False
    
    # Run PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(spec_file),
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            check=True,
            capture_output=False,
        )
        print("Build complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("Error: PyInstaller not found. Install it with: pip install pyinstaller")
        return False


def verify_build(project_root: Path) -> bool:
    """
    Verify that the build was successful.
    
    Args:
        project_root: Project root directory
        
    Returns:
        True if verification passed, False otherwise
    """
    print("Verifying build...")
    
    exe_path = project_root / "dist" / "AutoThanksClicker.exe"
    
    if not exe_path.exists():
        print(f"Error: Executable not found: {exe_path}")
        return False
    
    # Check file size (should be at least a few MB)
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"  Executable size: {size_mb:.2f} MB")
    
    if size_mb < 1:
        print("Warning: Executable seems too small, may be incomplete")
        return False
    
    print(f"  Executable path: {exe_path}")
    print("Verification passed.")
    return True


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Build Auto Thanks Clicker executable"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the built executable exists after building"
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean build artifacts, don't build"
    )
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    # Clean if requested
    if args.clean or args.clean_only:
        clean_build_artifacts(project_root)
        if args.clean_only:
            return 0
    
    # Build
    if not build_executable(project_root):
        return 1
    
    # Verify if requested
    if args.verify:
        if not verify_build(project_root):
            return 1
    
    print("\nBuild successful!")
    print(f"Executable: {project_root / 'dist' / 'AutoThanksClicker.exe'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
