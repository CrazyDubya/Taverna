#!/usr/bin/env python3
"""Script to clean up whitespace in Python files."""
import sys

def clean_file(filename):
    """Clean up whitespace in the specified file."""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Remove trailing whitespace and normalize line endings
    cleaned_lines = [line.rstrip() + '\n' for line in lines]
    
    # Write cleaned content back to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        clean_file(sys.argv[1])
    else:
        print("Usage: python clean_whitespace.py <filename>")
