# -*- coding: utf-8 -*-
"""
Quick fix script to replace status_bar.showMessage with safe_status_message
"""

import re
from pathlib import Path

# Read the file
browser_path = Path(__file__).parent / "browser.py"
with open(browser_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace self.status_bar.showMessage with self.safe_status_message
# But NOT in the safe_status_message function itself
pattern = r'self\.status_bar\.showMessage\('
replacement = r'self.safe_status_message('

# Count occurrences
count = len(re.findall(pattern, content))
print(f"Found {count} occurrences of self.status_bar.showMessage(")

# Replace all
content_new = re.sub(pattern, replacement, content)

# Write back
with open(browser_path, 'w', encoding='utf-8') as f:
    f.write(content_new)

print(f"✓ Replaced all {count} occurrences")
print("Done!")
