#!/usr/bin/env python3
"""
Version bumping utility for Clusterm
"""

import sys
import re
from pathlib import Path
from typing import Tuple

def get_current_version() -> Tuple[int, int, int]:
    """Get current version from __version__.py"""
    version_file = Path(__file__).parent.parent / "src" / "__version__.py"
    content = version_file.read_text()
    
    # Extract version info
    major_match = re.search(r'MAJOR = (\d+)', content)
    minor_match = re.search(r'MINOR = (\d+)', content)  
    patch_match = re.search(r'PATCH = (\d+)', content)
    
    if not all([major_match, minor_match, patch_match]):
        raise ValueError("Could not parse version from __version__.py")
    
    return (
        int(major_match.group(1)),
        int(minor_match.group(1)), 
        int(patch_match.group(1))
    )

def bump_version(version_type: str) -> Tuple[int, int, int]:
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

def update_version_file(major: int, minor: int, patch: int):
    """Update the __version__.py file with new version"""
    version_file = Path(__file__).parent.parent / "src" / "__version__.py"
    content = version_file.read_text()
    
    # Update version components
    content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{major}.{minor}.{patch}"', content)
    content = re.sub(r'__version_info__ = \([^)]*\)', f'__version_info__ = ({major}, {minor}, {patch})', content)
    content = re.sub(r'MAJOR = \d+', f'MAJOR = {major}', content)
    content = re.sub(r'MINOR = \d+', f'MINOR = {minor}', content)
    content = re.sub(r'PATCH = \d+', f'PATCH = {patch}', content)
    content = re.sub(r'VERSION_STRING = f"[^"]*"', f'VERSION_STRING = f"{major}.{minor}.{patch}"', content)
    
    version_file.write_text(content)

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
        
        update_version_file(new_major, new_minor, new_patch)
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