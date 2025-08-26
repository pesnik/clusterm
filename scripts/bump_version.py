#!/usr/bin/env python3
"""
Version bumping utility for Clusterm
"""

import re
import sys
from pathlib import Path


def get_current_version() -> tuple[int, int, int]:
    """Get current version from pyproject.toml"""
    pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject_file.read_text()

    # Extract version from pyproject.toml
    version_match = re.search(r'version = "(\d+)\.(\d+)\.(\d+)"', content)

    if not version_match:
        raise ValueError("Could not parse version from pyproject.toml")

    return (
        int(version_match.group(1)),
        int(version_match.group(2)),
        int(version_match.group(3))
    )

def bump_version(version_type: str) -> tuple[int, int, int]:
    """Bump version based on type (major, minor, patch)"""
    major, minor, patch = get_current_version()

    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid version type: {version_type}. Use: major, minor, or patch")

    return major, minor, patch

def update_version_files(major: int, minor: int, patch: int):
    """Update version in both pyproject.toml and __version__.py"""
    new_version = f"{major}.{minor}.{patch}"

    # Update pyproject.toml
    pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
    pyproject_content = pyproject_file.read_text()
    pyproject_content = re.sub(
        r'version = "\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        pyproject_content
    )
    pyproject_file.write_text(pyproject_content)

    # Update __version__.py
    version_file = Path(__file__).parent.parent / "src" / "__version__.py"
    version_content = version_file.read_text()

    # Update all version references
    version_content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{new_version}"', version_content)
    version_content = re.sub(r'__version_info__ = \([^)]*\)', f'__version_info__ = ({major}, {minor}, {patch})', version_content)
    version_content = re.sub(r'MAJOR = \d+', f'MAJOR = {major}', version_content)
    version_content = re.sub(r'MINOR = \d+', f'MINOR = {minor}', version_content)
    version_content = re.sub(r'PATCH = \d+', f'PATCH = {patch}', version_content)
    version_content = re.sub(r'VERSION_STRING = f"[^"]*"', f'VERSION_STRING = f"{new_version}"', version_content)

    version_file.write_text(version_content)

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py <major|minor|patch>")
        sys.exit(1)

    version_type = sys.argv[1].lower()

    try:
        current_major, current_minor, current_patch = get_current_version()
        print(f"Current version: {current_major}.{current_minor}.{current_patch}")

        new_major, new_minor, new_patch = bump_version(version_type)
        print(f"New version: {new_major}.{new_minor}.{new_patch}")

        # Confirm with user
        response = input(f"Bump version to {new_major}.{new_minor}.{new_patch}? (y/N): ")
        if response.lower() != 'y':
            print("Version bump cancelled")
            sys.exit(0)

        update_version_files(new_major, new_minor, new_patch)
        print(f"✅ Version bumped to {new_major}.{new_minor}.{new_patch}")
        print("\nNext steps:")
        print("1. Update CHANGELOG.md with release notes")
        print(f"2. git add -A && git commit -m 'Bump version to {new_major}.{new_minor}.{new_patch}'")
        print(f"3. git tag v{new_major}.{new_minor}.{new_patch}")
        print("4. git push origin main --tags")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
