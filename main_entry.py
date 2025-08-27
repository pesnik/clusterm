#!/usr/bin/env python3
"""
Entry point for PyInstaller binary - avoids relative import issues
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import and run main
from clusterm.__main__ import main

if __name__ == "__main__":
    main()