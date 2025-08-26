#!/usr/bin/env python3
"""
Complete release management script for Clusterm
Handles version bumping, changelog updates, git operations, and tagging
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_current_version() -> tuple[int, int, int]:
    """Get current version from pyproject.toml"""
    pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject_file.read_text()

    version_match = re.search(r'version = "(\d+)\.(\d+)\.(\d+)"', content)
    if not version_match:
        raise ValueError("Could not parse version from pyproject.toml")

    return (
        int(version_match.group(1)),
        int(version_match.group(2)),
        int(version_match.group(3))
    )


def bump_version(version_type: str) -> tuple[int, int, int]:
    """Bump version based on type"""
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
        raise ValueError(f"Invalid version type: {version_type}")

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

    version_content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{new_version}"', version_content)
    version_content = re.sub(r'__version_info__ = \([^)]*\)', f'__version_info__ = ({major}, {minor}, {patch})', version_content)
    version_content = re.sub(r'MAJOR = \d+', f'MAJOR = {major}', version_content)
    version_content = re.sub(r'MINOR = \d+', f'MINOR = {minor}', version_content)
    version_content = re.sub(r'PATCH = \d+', f'PATCH = {patch}', version_content)
    version_content = re.sub(r'VERSION_STRING = f"[^"]*"', f'VERSION_STRING = f"{new_version}"', version_content)

    version_file.write_text(version_content)


def get_git_changes() -> list[str]:
    """Get list of changes since last release"""
    try:
        # Get latest tag
        result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            last_tag = result.stdout.strip()
            # Get commits since last tag
            result = subprocess.run(['git', 'log', f'{last_tag}..HEAD', '--oneline'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except Exception:
        pass

    # Fallback to recent commits
    try:
        result = subprocess.run(['git', 'log', '--oneline', '-10'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[:5]  # Last 5 commits
    except Exception:
        pass

    return []


def update_changelog(version: str, changes: list[str]):
    """Update CHANGELOG.md with new version"""
    changelog_file = Path(__file__).parent.parent / "CHANGELOG.md"

    if not changelog_file.exists():
        print("⚠️  CHANGELOG.md not found, skipping changelog update")
        return

    # Read current changelog
    current_content = changelog_file.read_text()

    # Create new entry
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"\n## [{version}] - {date_str}\n\n"

    if changes:
        new_entry += "### Changes\n"
        for change in changes:
            # Clean up git commit format
            clean_change = re.sub(r'^[a-f0-9]+\s+', '- ', change.strip())
            if clean_change.startswith('-'):
                new_entry += f"{clean_change}\n"
            else:
                new_entry += f"- {clean_change}\n"
    else:
        new_entry += "### Changes\n- Minor updates and improvements\n"

    # Insert new entry after the first ## heading
    lines = current_content.split('\n')
    insert_index = 0

    for i, line in enumerate(lines):
        if line.startswith('## [') and 'Unreleased' not in line:
            insert_index = i
            break
        elif line.startswith('## ') and i > 0:  # Any ## heading after the first
            insert_index = i
            break

    # Insert new entry
    lines.insert(insert_index, new_entry.rstrip())
    changelog_file.write_text('\n'.join(lines))


def run_git_operations(version: str):
    """Handle git operations for release"""
    try:
        # Add all changes
        subprocess.run(['git', 'add', '-A'], check=True)

        # Commit changes
        commit_msg = f"Release v{version}\n\nBumped version to {version}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

        # Create tag
        tag_msg = f"Release v{version}"
        subprocess.run(['git', 'tag', '-a', f'v{version}', '-m', tag_msg], check=True)

        print("✅ Git operations completed:")
        print("   - Committed changes")
        print(f"   - Created tag v{version}")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False


def main():
    """Main release function"""
    if len(sys.argv) != 2:
        print("Usage: python release.py <major|minor|patch>")
        print("\nExamples:")
        print("  python release.py patch   # 0.2.0 -> 0.2.1")
        print("  python release.py minor   # 0.2.0 -> 0.3.0")
        print("  python release.py major   # 0.2.0 -> 1.0.0")
        sys.exit(1)

    version_type = sys.argv[1].lower()

    try:
        print("🚀 Clusterm Release Manager")
        print("=" * 40)

        # Get current version
        current_major, current_minor, current_patch = get_current_version()
        current_version = f"{current_major}.{current_minor}.{current_patch}"
        print(f"Current version: {current_version}")

        # Calculate new version
        new_major, new_minor, new_patch = bump_version(version_type)
        new_version = f"{new_major}.{new_minor}.{new_patch}"
        print(f"New version: {new_version}")

        # Get changes since last release
        changes = get_git_changes()
        if changes:
            print(f"\nRecent changes ({len(changes)} commits):")
            for change in changes[:5]:  # Show first 5
                print(f"  • {change}")

        # Confirm with user
        response = input(f"\n🎯 Create release v{new_version}? (y/N): ")
        if response.lower() != 'y':
            print("❌ Release cancelled")
            sys.exit(0)

        print(f"\n📝 Preparing release v{new_version}...")

        # Update version files
        update_version_files(new_major, new_minor, new_patch)
        print("✅ Updated version files")

        # Update changelog
        update_changelog(new_version, changes)
        print("✅ Updated CHANGELOG.md")

        # Git operations
        if run_git_operations(new_version):
            print(f"\n🎉 Release v{new_version} completed successfully!")
            print("\n📋 Next steps:")
            print(f"   1. Review the changes: git show v{new_version}")
            print("   2. Push to remote: git push origin main --tags")
            print("   3. Create GitHub release (optional)")
            print("   4. Deploy to production (if applicable)")
        else:
            print("\n❌ Release failed during git operations")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Release failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
