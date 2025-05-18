#!/usr/bin/env python3
"""Script to fix test file imports and formatting."""
import os
import re
from pathlib import Path

def fix_test_file(filepath):
    """Fix imports and formatting in a test file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add missing imports
    if 'test_llm_parser.py' in str(filepath):
        if 'import pytest' not in content:
            content = content.replace(
                '"""Tests for the LLM parser module."""',
                '"""Tests for the LLM parser module."""\n\nimport pytest'
            )
    
    # Fix missing imports in test_meta_quest.py
    elif 'test_meta_quest.py' in str(filepath):
        if 'from unittest.mock import patch' not in content:
            content = content.replace(
                '"""Tests for the meta quest system."""',
                '"""Tests for the meta quest system."""\n\nfrom unittest.mock import patch\nfrom core.game_state import GameState'
            )
    
    # Fix missing imports in test_npc_integration.py
    elif 'test_npc_integration.py' in str(filepath):
        # Remove duplicate class definitions
        content = re.sub(
            r'class (PlayerState|Inventory).*?\n\n',
            '',
            content,
            flags=re.DOTALL
        )
        
        # Remove unused variable assignments
        content = content.replace("spawn_unsub = ", "_ = ")  # Mark as intentionally unused
    
    # Write fixed content back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_test_formatting(filepath):
    """Fix formatting issues in test files."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    in_class = False
    in_function = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Fix missing blank lines before class/function definitions
        if stripped.startswith(('class ', 'def ')) and not in_function:
            if in_class and not new_lines[-1].strip() == '':
                new_lines.append('\n')
            if not in_class and i > 0 and lines[i-1].strip() != '':
                new_lines.append('\n')
        
        # Track class/function scope
        if stripped.startswith('class '):
            in_class = True
            in_function = False
        elif stripped.startswith('def '):
            in_function = True
        elif stripped == '':
            in_function = False
        
        # Fix E128 continuation line under-indented
        if '    ' in line and not line.startswith('    '):
            if any(c in line for c in '([{'):
                line = '    ' + line.lstrip()
        
        # Fix E231 missing whitespace after comma
        line = re.sub(r',(\S)', r', \1', line)
        
        # Fix E501 line too long (ignore test data and docstrings)
        if len(line) > 100 and not any(s in line for s in ['http', 'test_data', '"""']):
            # Simple line break for long lines (can be improved)
            if '=' in line and len(line) - line.find('=') > 30:
                parts = line.split('=')
                line = f"{parts[0]}= (\n    {parts[1].lstrip()}"
            elif '(' in line and ')' in line and line.index(')') > line.index('(') + 30:
                # Break long function calls
                before_paren = line[:line.index('(') + 1]
                after_paren = line[line.index(')'):]
                params = line[line.index('(') + 1:line.rindex(')')]
                param_list = [p.strip() for p in params.split(',')]
                if len(param_list) > 1:
                    new_params = ',\n    '.join(param_list)
                    line = f"{before_paren}\n    {new_params}\n){after_paren}"
        
        new_lines.append(line)
    
    # Ensure exactly two blank lines at end of file
    while new_lines and new_lines[-1].strip() == '':
        new_lines.pop()
    new_lines.append('\n\n')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def process_test_files(directory):
    """Process all test files in the given directory."""
    test_files = list(Path(directory).rglob('test_*.py'))
    
    for filepath in test_files:
        print(f"Processing {filepath}...")
        fix_test_file(filepath)
        fix_test_formatting(filepath)
        
        # Run autopep8 to fix remaining style issues
        os.system(f'autopep8 --in-place --aggressive {filepath}')

if __name__ == '__main__':
    process_test_files('tests/')
    print("Test files have been formatted.")
