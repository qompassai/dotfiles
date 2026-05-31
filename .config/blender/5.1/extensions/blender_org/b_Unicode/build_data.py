import os
import json
import ast
import unicodedata

# 1. READ EXISTING CATEGORIES FROM __init__.py
base_dir = '/home/mad-max/.config/blender/5.2/extensions/blender_org/b_Unicode'
init_file = os.path.join(base_dir, '__init__.py')

with open(init_file, 'r', encoding='utf-8') as f:
    init_content = f.read()

# We can parse the dict out by regex or ast
import re

cat_match = re.search(r'UNICODE_CATEGORIES\s*=\s*({.*?})', init_content, re.DOTALL)
if cat_match:
    try:
        old_categories = ast.literal_eval(cat_match.group(1))
    except:
        print("Could not evaluate UNICODE_CATEGORIES using ast.")
        old_categories = {}
else:
    old_categories = {}

# We also want to keep tooltips dynamically like in the macro:
# tooltip = f"{char}  —  {name}  (U+{base_cp:04X})"
def get_char_tooltip(char, name=None):
    base_cp = ord(char[0])
    if not name:
        try:
            name = unicodedata.name(char[0])
        except ValueError:
            name = "UNKNOWN"
    return f"{char}  —  {name}  (U+{base_cp:04X})"

# 2. PARSE THE 3 TXT FILES
new_categories = {}
all_tooltips = {}

def process_char(char, group, name):
    if group not in new_categories:
        new_categories[group] = []
    if char not in new_categories[group]:
        new_categories[group].append(char)
    if char not in all_tooltips:
        all_tooltips[char] = get_char_tooltip(char, name)

# Parse emoji-test.txt
emoji_test_file = os.path.join(base_dir, 'emoji-test.txt')
current_group = "Other"
with open(emoji_test_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('# group:'):
            current_group = line.split(':', 1)[1].strip()
        elif line and not line.startswith('#'):
            if ';' in line:
                part1, part2 = line.split(';', 1)
                codepoints_str = part1.strip()
                status_part, comment_part = part2.split('#', 1)
                status = status_part.strip()
                if status in ('fully-qualified', 'component'):
                    parts = comment_part.strip().split(' ', 2)
                    if len(parts) >= 3:
                        emoji_char = parts[0]
                        emoji_name = parts[2]
                        process_char(emoji_char, current_group, emoji_name)

# Parse emoji-zwj-sequences.txt
zwj_file = os.path.join(base_dir, 'emoji-zwj-sequences.txt')
with open(zwj_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            if ';' in line:
                part1, part2 = line.split(';', 1)
                hex_codes = part1.strip().split()
                char = "".join(chr(int(h, 16)) for h in hex_codes)
                
                status_part, comment_part = part2.split('#', 1)
                # the status_part has type and description:  RGI_Emoji_ZWJ_Sequence  ; couple with heart: man, man
                type_desc = status_part.split(';')
                if len(type_desc) == 2:
                    name = type_desc[1].strip()
                else:
                    name = "ZWJ Sequence"
                
                process_char(char, "ZWJ Sequences", name)

# Parse emoji-sequences.txt
seq_file = os.path.join(base_dir, 'emoji-sequences.txt')
with open(seq_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            if ';' in line:
                part1, part2 = line.split(';', 1)
                hex_ranges = part1.strip().split()
                
                status_part, comment_part = part2.split('#', 1)
                name = "Emoji Sequence"
                if ';' in status_part:
                    name = status_part.split(';')[1].strip()
                
                for h in hex_ranges:
                    if '..' in h:
                        start_h, end_h = h.split('..')
                        for cp in range(int(start_h, 16), int(end_h, 16) + 1):
                            process_char(chr(cp), "Emoji Sequences", name)
                    else:
                        process_char(chr(int(h, 16)), "Emoji Sequences", name)

# 3. MERGE EXISTING AND NEW
final_categories = {}

# Put old categories first to maintain structure
for cat, chars in old_categories.items():
    final_categories[cat] = []
    for c in chars:
        if c not in final_categories[cat]:
            final_categories[cat].append(c)
        if c not in all_tooltips:
            all_tooltips[c] = get_char_tooltip(c)

# Track seen characters so we don't duplicate them in "ZWJ Sequences" if they already got put in a main group
seen_chars = set()
for cat, chars in final_categories.items():
    seen_chars.update(chars)

# Add new categories (e.g., from emoji-test.txt and sequences)
for cat, chars in new_categories.items():
    if cat not in final_categories:
        final_categories[cat] = []
    for c in chars:
        if c not in seen_chars:
            final_categories[cat].append(c)
            seen_chars.add(c)

# Clean out empty categories
final_categories = {k: v for k,v in final_categories.items() if v}

# Identify unwanted characters (multi-codepoint, ZWJ sequences) and discarded (skin tones, duplicates)
discarded_chars = set()
unwanted_chars = set()

for char in all_tooltips.keys():
    # 1. Discard any character with a skin-tone modifier
    if any(0x1F3FB <= ord(c) <= 0x1F3FF for c in char):
        discarded_chars.add(char)
        continue
    
    # 2. Discard if it's a \ufe0f duplicate of a base character we already have
    if '\ufe0f' in char:
        base = char.replace('\ufe0f', '')
        if base in all_tooltips and base != char:
            discarded_chars.add(char)
            continue
            
    # 3. Mark the rest of complex multi-codepoint emojis (like ZWJ families) as "Unwanted"
    if len(char) > 1 or '\u200d' in char:
        unwanted_chars.add(char)

clean_categories = {}
unwanted_categories = {}

for cat, chars in final_categories.items():
    clean_c = []
    unw_c = []
    for c in chars:
        if c in discarded_chars or cat == 'Component':
            continue  # Completely remove these
        elif c in unwanted_chars:
            unw_c.append(c)
        else:
            clean_c.append(c)
    if clean_c:
        clean_categories[cat] = clean_c
    if unw_c:
        unwanted_categories[cat] = unw_c

clean_tooltips = {c: all_tooltips[c] for c in all_tooltips if c not in unwanted_chars and c not in discarded_chars and c not in final_categories.get('Component', [])}

out_data_clean = {}
for cat, chars in clean_categories.items():
    out_data_clean[cat] = {c: clean_tooltips[c] for c in chars if c in clean_tooltips}

# Write to unicode_data.json
out_file = os.path.join(base_dir, 'unicode_data.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(out_data_clean, f, ensure_ascii=False, indent=2)

print(f"Data built and saved.")
print(f"Categories generated: {list(clean_categories.keys())}")
print(f"Total categories: {len(clean_categories)}")
print(f"Clean characters: {len(clean_tooltips)}")
