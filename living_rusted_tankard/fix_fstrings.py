#!/usr/bin/env python3
"""Fix unnecessary f-strings that have no placeholders."""

import re
import sys
from pathlib import Path


def fix_f_strings_in_file(filepath):
    """Remove f-prefix from strings that have no placeholders."""
    with open(filepath, "r") as f:
        content = f.read()

    original = content

    # Match f-strings (single or triple quoted) that don't contain {placeholders}
    # Single quoted f-strings without placeholders
    content = re.sub(r'"([^"{]*)"', lambda m: f'"{m.group(1)}"' if "{" not in m.group(1) else m.group(0), content)
    content = re.sub(r"'([^'{]*)'", lambda m: f"'{m.group(1)}'" if "{" not in m.group(1) else m.group(0), content)

    # Triple quoted f-strings without placeholders
    content = re.sub(r'"""([^{]*)"""', lambda m: f'"""{m.group(1)}"""' if "{" not in m.group(1) else m.group(0), content)
    content = re.sub(r"'''([^{]*)'''", lambda m: f"'''{m.group(1)}'''" if "{" not in m.group(1) else m.group(0), content)

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        return True
    return False


def main():
    """Fix f-strings in all Python files."""
    count = 0
    for filepath in Path(".").rglob("*.py"):
        if any(part in str(filepath) for part in [".venv", ".git", "__pycache__", ".pytest_cache"]):
            continue

        if fix_f_strings_in_file(filepath):
            count += 1
            print(f"Fixed: {filepath}")

    print(f"\nTotal files modified: {count}")


if __name__ == "__main__":
    main()
