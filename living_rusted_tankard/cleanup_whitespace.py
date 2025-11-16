#!/usr/bin/env python3
"""Script to clean up whitespace in Python files."""
import os
import sys
from pathlib import Path


def clean_file(filepath):
    """Clean up whitespace in the specified file."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Remove trailing whitespace and normalize line endings
    cleaned_lines = [line.rstrip() + "\n" for line in lines]

    # Remove empty whitespace lines
    cleaned_lines = [line if line.strip() else "\n" for line in cleaned_lines]

    # Write cleaned content back to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print(f"Cleaned {filepath}")


def fix_imports(filepath):
    """Ensure proper spacing around imports and code."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    in_imports = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check if we're in the imports section
        if stripped.startswith(("import ", "from ")):
            if not in_imports and i > 0 and lines[i - 1].strip():
                new_lines.append("\n")
            in_imports = True
            new_lines.append(line)
        elif in_imports and not stripped:
            new_lines.append("\n")
            in_imports = False
        else:
            if in_imports and not stripped:
                in_imports = False
                new_lines.append("\n")
            new_lines.append(line)

    # Ensure two newlines after imports
    if new_lines and new_lines[-1].strip():
        new_lines.append("\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def process_directory(directory):
    """Process all Python files in the given directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                clean_file(filepath)
                fix_imports(filepath)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isfile(target):
            clean_file(target)
            fix_imports(target)
        elif os.path.isdir(target):
            process_directory(target)
        else:
            print(f"Error: {target} is not a valid file or directory")
    else:
        print("Usage: python cleanup_whitespace.py <file_or_directory>")
        print("Cleaning current directory...")
        process_directory(".")
