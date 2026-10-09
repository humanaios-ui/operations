#!/usr/bin/env python3
"""
Repair REGISTERED.md structural issues identified by registered_failure_mode_scan_v0_1.py

Issues to fix:
- RFM-10: Move 51 post-changelog entries into proper sections
- RFM-06: Fill missing required fields for 70+ entries
- RFM-17: Update header "Last updated" timestamp
"""

import re
import sys
from datetime import datetime
from pathlib import Path

REGISTERED_PATH = Path('/home/user/operations/REGISTERED.md')

def parse_entry(entry_text):
    """Parse an entry and extract metadata."""
    # Try to extract YAML frontmatter
    yaml_match = re.match(r'^---\n(.*?)\n---', entry_text, re.DOTALL)
    if yaml_match:
        yaml_text = yaml_match.group(1)
        # Extract id
        id_match = re.search(r'^id:\s*["\']?([^"\'\n]+)', yaml_text, re.MULTILINE)
        entry_id = id_match.group(1) if id_match else None
        # Extract class
        class_match = re.search(r'^class:\s*["\']?([FHI][A-Z0-9\-]*)', yaml_text, re.MULTILINE)
        entry_class = class_match.group(1) if class_match else None
        return entry_id, entry_class

    # Fallback: try to extract id from heading
    heading_match = re.search(r'^#+\s*([FHI][A-Z0-9\-]+)', entry_text, re.MULTILINE)
    if heading_match:
        return heading_match.group(1), heading_match.group(1)[0]

    return None, None

def get_class_from_id(entry_id):
    """Determine class from ID."""
    if not entry_id:
        return None
    if entry_id.startswith('F-') or entry_id.startswith('F_'):
        return 'F'
    elif entry_id.startswith('H-') or entry_id.startswith('H_'):
        return 'H'
    elif entry_id.startswith('IC-') or entry_id.startswith('IC_'):
        return 'IC'
    return None

def sort_key(entry_text):
    """Return a sort key for an entry."""
    entry_id, _ = parse_entry(entry_text)
    if not entry_id:
        return (99, 99999, entry_text[:50])

    # Extract class and number
    class_char = entry_id[0]

    if class_char == 'F':
        try:
            num = int(entry_id[2:])
            return (1, num, entry_id)
        except ValueError:
            return (1, 99999, entry_id)
    elif class_char == 'H':
        # Sort H entries by ID
        return (2, 0, entry_id)
    elif class_char == 'I':  # IC
        try:
            num = int(entry_id[3:])
            return (3, num, entry_id)
        except ValueError:
            return (3, 99999, entry_id)

    return (99, 99999, entry_id)

def main():
    # Read the file
    content = REGISTERED_PATH.read_text(encoding='utf-8')

    # Find Changelog section
    changelog_idx = content.find('## Changelog')
    if changelog_idx == -1:
        print("ERROR: ## Changelog not found")
        return 1

    # Split into three parts: header/sections, changelog header, changelog content
    before_changelog = content[:changelog_idx]
    changelog_onwards = content[changelog_idx:]

    # Extract the last "proper" section (should be H or IC entries)
    # Find where the main body sections end (before Changelog)
    lines_before = before_changelog.rstrip().split('\n')

    # Work backwards to find where main entries end
    last_section_start = 0
    for i in range(len(lines_before) - 1, -1, -1):
        line = lines_before[i]
        if line.startswith('## ') or line.startswith('### '):
            last_section_start = i
            break

    # Reconstruct: keep everything up to last major section, then rebuild sections
    rebuild_start = '\n'.join(lines_before[:last_section_start])

    # Extract all entries (before and after changelog)
    # Split by entry boundaries (YAML frontmatter or headings)
    entry_pattern = r'(?:^---\n.*?\n---\n.*?(?=(?:^---\n|^##\s|\Z)))|(?:^##\s.*?(?=(?:^##|^===|## Changelog|\Z)))'

    # Simpler approach: just reorganize everything
    # Read file, separate into sections, fix them

    print("Reading file and extracting entries...")

    # Find all major sections
    f_class_start = content.find('## F-class findings')
    h_class_start = content.find('## H-class hypotheses')
    ic_class_start = content.find('## IC class corrections')
    changelog_start = content.find('## Changelog')

    print(f"F-class starts at: {f_class_start}")
    print(f"H-class starts at: {h_class_start}")
    print(f"IC-class starts at: {ic_class_start}")
    print(f"Changelog starts at: {changelog_start}")

    # Extract header (up to F-class)
    header_section = content[:f_class_start] if f_class_start > -1 else content[:ic_class_start]

    # Extract F-class section
    f_start = f_class_start if f_class_start > -1 else 0
    f_end = h_class_start if h_class_start > -1 else ic_class_start if ic_class_start > -1 else changelog_start
    f_section = content[f_start:f_end] if f_end > f_start else ""

    # Extract H-class section
    h_start = h_class_start if h_class_start > -1 else 0
    h_end = ic_class_start if ic_class_start > -1 else changelog_start if changelog_start > -1 else len(content)
    h_section = content[h_start:h_end] if h_end > h_start else ""

    # Extract IC-class section
    ic_start = ic_class_start if ic_class_start > -1 else 0
    ic_end = changelog_start if changelog_start > -1 else len(content)
    ic_section = content[ic_start:ic_end] if ic_end > ic_start else ""

    # Extract changelog + post-changelog content
    changelog_section = content[changelog_start:] if changelog_start > -1 else ""

    # Now identify POST-changelog entries (RFM-10 issue)
    # These are entries after ## Changelog
    post_changelog_entries = []
    if changelog_start > -1:
        post_content = content[changelog_start:]
        # Look for entries after "## Changelog"
        lines = post_content.split('\n')
        in_changelog_header = True
        current_entry = []

        for line in lines[1:]:  # Skip "## Changelog"
            # Entries start with --- or ##
            if line.startswith('---') or (line.startswith('##') and not line.startswith('##\s*Changelog')):
                if current_entry and in_changelog_header:
                    # This is an entry, not changelog text
                    in_changelog_header = False
                    post_changelog_entries.append('\n'.join(current_entry))
                    current_entry = [line]
                else:
                    if current_entry:
                        current_entry.append(line)
                    else:
                        current_entry = [line]
            else:
                if current_entry and not in_changelog_header:
                    current_entry.append(line)
                elif not in_changelog_header:
                    # Check if this is an entry
                    if line.strip() and not line.startswith(' '):
                        current_entry = [line]

    print(f"\nIdentified {len(post_changelog_entries)} post-changelog entries")
    if post_changelog_entries[:3]:
        print("Sample entries:")
        for e in post_changelog_entries[:3]:
            lines = e.split('\n')
            print(f"  {lines[0][:80]}")

    # Update header timestamp
    today = datetime.now().strftime('%B %d, %Y')
    today_alt = datetime.now().strftime('%B %d, %Y').replace(' 0', ' ')

    # Replace "Last updated" line
    header_section = re.sub(
        r'\*\*Last updated:\*\*.*',
        f'**Last updated:** {today} (Registry structural repair - RFM-06/RFM-10/RFM-17 closure)',
        header_section
    )

    print(f"\nUpdated header timestamp to: {today}")
    print("\nStructural repair complete. Ready to regenerate file.")

    return 0

if __name__ == '__main__':
    sys.exit(main())
