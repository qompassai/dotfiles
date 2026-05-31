import json, re

try:
    with open('unicode_data.json','r') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading unicode_data.json: {e}")
    data = {}

for cat, subs in data.items():
    for sub in subs:
        safe_cat = cat.replace(' ','').replace('&','n')
        safe_sub = sub.replace(' ','_').replace('-','_').replace('&','n')
        idname = f'TEXT_PT_unicode_{safe_cat}_{safe_sub}'
        if not re.match(r'^[A-Za-z0-9_]+$', idname):
            print(f'INVALID ID format: {idname}')

        # Blender 2.8+ idnames have an upper limit on length, often 63 characters
        if len(idname) >= 64:
            print(f'IDNAME TOO LONG: {idname} (len {len(idname)})')

import bpy_types
from bl_ui import space_text
