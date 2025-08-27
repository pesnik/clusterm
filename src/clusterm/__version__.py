"""Version information for Clusterm
"""

__version__ = "0.4.0"
__version_info__ = (0, 4, 0)

# Release information
MAJOR = 0
MINOR = 4
PATCH = 0

# Version string for display
VERSION_STRING = "0.4.0"

# Release notes for current version
RELEASE_NOTES = """
Clusterm v0.4.0 - Binary Distribution & Helm Context Release

🚀 New Features:
- PyInstaller Linux binary distribution (~18MB standalone executable)
- Context-aware helm chart selection with auto-selection
- Enhanced helm command working directory resolution
- Chart selection visual feedback in status panel
- Support for helm show commands with proper chart context

🔧 Improvements:
- Auto-select first chart when charts are loaded
- Better chart selection debugging and logging
- Improved helm command path resolution for local charts
- Enhanced status panel with selected chart display
- Fixed launch.json for proper package debugging

🏗️ Architecture:
- Self-contained binary with no Python dependencies required
- Comprehensive PyInstaller configuration for textual UI
- Automated build system with build.py script
- Improved package structure for binary distribution

📦 Distribution:
- Standalone Linux binary (x86_64)
- Compatible with Ubuntu 20.04+, CentOS 8+
- No Python installation required on target systems
- Simple installation via binary download
"""
