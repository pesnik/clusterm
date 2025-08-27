# Building Clusterm Binary

This document explains how to build a standalone Linux binary for clusterm using PyInstaller.

## Quick Build

```bash
# Build the binary
uv run python build.py

# Or build manually
uv run pyinstaller --clean clusterm.spec
```

## Prerequisites

- Python 3.11+
- uv package manager
- Linux environment (for Linux binary)

## Build Process

1. **Install build dependencies:**
   ```bash
   uv sync --group build
   ```

2. **Run the automated build:**
   ```bash
   uv run python build.py
   ```

   Or manually:
   ```bash
   uv run pyinstaller --clean clusterm.spec
   ```

3. **Binary location:**
   ```
   dist/clusterm    # Standalone Linux binary (~18MB)
   ```

## Testing the Binary

```bash
# Test startup (will timeout after 3s - this is expected for TUI)
timeout 3 ./dist/clusterm

# Check binary info
file dist/clusterm
ls -la dist/clusterm
```

## Installation

### System-wide installation:
```bash
sudo cp dist/clusterm /usr/local/bin/
clusterm  # Run from anywhere
```

### Local installation:
```bash
# Add to PATH temporarily
export PATH=$PATH:$(pwd)/dist

# Or create symlink in local bin
mkdir -p ~/.local/bin
ln -s $(pwd)/dist/clusterm ~/.local/bin/
# Make sure ~/.local/bin is in your PATH
```

## Distribution

The binary is self-contained and includes:
- All Python dependencies
- Textual UI framework
- YAML parsing libraries
- Prompt toolkit for interactive input

### Requirements for target systems:
- Linux x86_64
- GLIBC 2.31+ (compatible with Ubuntu 20.04+, CentOS 8+, etc.)
- No Python installation required

### Binary details:
- **Size:** ~18MB
- **Type:** ELF 64-bit executable
- **Dependencies:** Dynamic linking to system libraries only
- **Architecture:** x86_64 Linux

## Troubleshooting

### Build Issues

1. **Missing textual modules:**
   - The spec file includes comprehensive hiddenimports for textual
   - If you see textual import errors, add them to `hiddenimports` in `clusterm.spec`

2. **Relative import errors:**
   - Uses `main_entry.py` to avoid relative import issues
   - Ensures proper PYTHONPATH setup

3. **Missing dependencies:**
   - Run `uv sync --group build` to install PyInstaller
   - All runtime dependencies are included automatically

### Runtime Issues

1. **TUI display problems:**
   - Ensure terminal supports ANSI colors and cursor control
   - Try running in different terminal emulators

2. **Permission errors:**
   - Make binary executable: `chmod +x dist/clusterm`
   - For system installation: use `sudo` for `/usr/local/bin/`

## Development

### Modifying the build:

1. **Update spec file:** Edit `clusterm.spec`
   - Add new `hiddenimports` for missing modules
   - Include additional `datas` for resource files

2. **Update build script:** Edit `build.py`
   - Modify build commands or add new steps
   - Customize testing or validation

3. **Rebuild:**
   ```bash
   uv run python build.py
   ```

### Build artifacts:
```
build/          # PyInstaller build cache
dist/clusterm   # Final binary
*.spec          # PyInstaller specification
main_entry.py   # Binary entry point
```

## Continuous Integration

For automated builds, use:

```bash
# Install dependencies
uv sync --group build

# Build binary
uv run pyinstaller --clean clusterm.spec

# Verify binary
file dist/clusterm
```

The binary can then be uploaded as a release artifact or distributed via package repositories.