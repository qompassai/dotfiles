import json

UNICODE_CATEGORIES = {}
with open('unicode_data.json', 'r') as f:
    for cat, subgroups in json.load(f).items():
        UNICODE_CATEGORIES[cat] = list(subgroups.keys())

def _make_subpanel_poll(category_name):
    def poll(active_category):
        return active_category == category_name
    return poll

polls = {}
for category, subgroups in UNICODE_CATEGORIES.items():
    polls[category] = _make_subpanel_poll(category)

print("Poll for Food & Drink with 'Food & Drink':", polls['Food & Drink']('Food & Drink'))
