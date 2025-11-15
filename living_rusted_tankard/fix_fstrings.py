#!/usr/bin/env python3
"""Fix f-strings that don't have placeholders."""
import re
import sys

def fix_fstrings_in_file(filepath):
    """Remove f prefix from f-strings without placeholders."""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern to match f-strings without placeholders
    # Matches f"..." or f'...' where there's no { inside

    # For double quotes: f"anything without { or }"
    pattern1 = r'f"([^"{]*)"'
    # For single quotes: f'anything without { or }'
    pattern2 = r"f'([^'{]*)'"

    def replace_if_no_placeholder(match):
        """Only replace if there's no placeholder in the string."""
        full_match = match.group(0)
        string_content = match.group(1)

        # Check if string contains { which indicates a placeholder
        if '{' not in string_content:
            # Remove the 'f' prefix
            return full_match[1:]  # Skip the 'f'
        return full_match

    content = re.sub(pattern1, replace_if_no_placeholder, content)
    content = re.sub(pattern2, replace_if_no_placeholder, content)

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

if __name__ == '__main__':
    files_to_fix = [
        'core/game_state.py',
        'core/npc_modules/goals.py',
        'core/npc_modules/interactions.py',
        'core/npc_modules/relationships.py',
        'core/npc_modules/secrets.py',
        'core/npc_systems/goals.py',
        'core/npc_systems/interactions.py',
        'core/npc_systems/relationships.py',
        'core/npc_systems/secrets.py',
        'core/time_display.py',
    ]

    fixed_count = 0
    for filepath in files_to_fix:
        try:
            if fix_fstrings_in_file(filepath):
                print(f"Fixed: {filepath}")
                fixed_count += 1
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    print(f"\nFixed {fixed_count} files")
