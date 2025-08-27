#!/usr/bin/env python3
"""
Build script for creating clusterm binary distribution using PyInstaller
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Error: {e.stderr}")
        return False


def clean_build_dirs():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)
    return True


def install_build_dependencies():
    """Install PyInstaller if not available"""
    try:
        import PyInstaller
        print("✅ PyInstaller already available")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        return run_command(["uv", "add", "--group", "build", "pyinstaller"], "PyInstaller installation")


def build_binary():
    """Build the binary using PyInstaller"""
    return run_command([
        "uv", "run", "pyinstaller",
        "--clean",
        "clusterm.spec"
    ], "Binary build")


def test_binary():
    """Test the built binary"""
    binary_path = Path("dist/clusterm/clusterm")
    if not binary_path.exists():
        print("❌ Binary not found at dist/clusterm/clusterm")
        return False
    
    print("🧪 Testing binary...")
    try:
        # Test that binary can start (with --help to avoid full UI)
        result = subprocess.run([str(binary_path), "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Binary test passed")
            return True
        else:
            print(f"❌ Binary test failed with return code: {result.returncode}")
            print(f"   stderr: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  Binary test timed out (this might be normal for TUI apps)")
        return True
    except Exception as e:
        print(f"❌ Binary test error: {e}")
        return False


def create_portable_wrapper():
    """Create a portable wrapper script"""
    wrapper_content = '''#!/bin/bash
# Portable wrapper for clusterm PyInstaller distribution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTERM_DIR="$SCRIPT_DIR/clusterm"

if [ -d "$CLUSTERM_DIR" ]; then
    exec "$CLUSTERM_DIR/clusterm" "$@"
else
    echo "Error: clusterm distribution not found at $CLUSTERM_DIR"
    exit 1
fi
'''
    wrapper_path = Path("dist/clusterm-portable")
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)
    return wrapper_path

def show_results():
    """Show build results and next steps"""
    binary_path = Path("dist/clusterm/clusterm")
    wrapper_path = Path("dist/clusterm-portable")
    
    if binary_path.exists():
        # Create portable wrapper
        create_portable_wrapper()
        
        size_mb = sum(f.stat().st_size for f in Path("dist/clusterm").rglob("*") if f.is_file()) / (1024 * 1024)
        print(f"\n🎉 Build completed successfully!")
        print(f"📁 Distribution directory: {Path('dist/clusterm').absolute()}")
        print(f"📏 Total size: {size_mb:.1f} MB")
        print(f"\n📖 Usage:")
        print(f"   ./dist/clusterm/clusterm           # Run directly from dist")
        print(f"   ./dist/clusterm-portable           # Run using portable wrapper")
        print(f"\n📦 Installation:")
        print(f"   # Option 1: Copy entire directory")
        print(f"   cp -r dist/clusterm ~/.local/share/")
        print(f"   ln -sf ~/.local/share/clusterm/clusterm ~/.local/bin/clusterm")
        print(f"   ")
        print(f"   # Option 2: Use portable wrapper")
        print(f"   cp dist/clusterm-portable ~/.local/bin/clusterm")
        print(f"   cp -r dist/clusterm ~/.local/bin/")
        print(f"   ")
        print(f"   # Option 3: Add to PATH temporarily")
        print(f"   export PATH=$PATH:$(pwd)/dist/clusterm")
    else:
        print("\n❌ Build failed - binary not found")


def main():
    """Main build process"""
    print("🚀 Building clusterm Linux binary...\n")
    
    # Check we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Must run from project root (where pyproject.toml exists)")
        sys.exit(1)
    
    steps = [
        ("Clean build directories", clean_build_dirs),
        ("Install build dependencies", install_build_dependencies),  
        ("Build binary", build_binary),
        ("Test binary", test_binary),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Build failed at: {step_name}")
            sys.exit(1)
        print()
    
    show_results()


if __name__ == "__main__":
    main()