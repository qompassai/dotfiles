import json

def get_bucket(subhead):
    s = subhead.lower()
    
    # 1. Geometry & Shapes
    if any(k in s for k in ['angle', 'circle', 'square', 'triangle', 'geometry']):
        return "Geometry & Shapes"
        
    # 2. Logic & Sets
    if any(k in s for k in ['logic', 'set', 'intersection', 'union', 'subset', 'superset']):
        return "Logic & Set Theory"
        
    # 3. Calculus & Advanced
    if any(k in s for k in ['integral', 'summation', 'n-ary', 'large operator', 'differential', 'infinity']):
        return "Calculus & Advanced"
        
    # 4. Arithmetic & Algebra
    if any(k in s for k in ['plus', 'minus', 'multiplication', 'division', 'fraction', 'root']):
        return "Arithmetic & Algebra"
        
    # 5. Relations & Misc
    # relation, relational, brackets, miscellaneous, etc.
    return "Relations & Symbols"

def main():
    with open('unicode_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    math_data = data.get("Math Operators", {})
    
    new_math_data = {
        "Arithmetic & Algebra": {},
        "Logic & Set Theory": {},
        "Geometry & Shapes": {},
        "Calculus & Advanced": {},
        "Relations & Symbols": {}
    }
    
    for subhead, chars in math_data.items():
        bucket = get_bucket(subhead)
        for char, tooltip in chars.items():
            
            # Additional fallback by character description if the subhead was too generic
            desc = tooltip.lower()
            if bucket == "Relations & Symbols":
                if any(x in desc for x in ['plus', 'minus', 'multiply', 'divide', 'fraction', 'root', 'asterisk', 'dot operator']):
                    bucket = "Arithmetic & Algebra"
                elif any(x in desc for x in ['integral', 'summation', 'infinity', 'differential']):
                    bucket = "Calculus & Advanced"
                elif any(x in desc for x in ['logic', 'set', 'union', 'intersection', 'element of']):
                    bucket = "Logic & Set Theory"
                elif any(x in desc for x in ['angle', 'circle', 'square', 'triangle', 'parallel', 'perpendicular']):
                    bucket = "Geometry & Shapes"
            
            new_math_data[bucket][char] = tooltip

    # Clean empty buckets just in case
    new_math_data = {k: v for k, v in new_math_data.items() if v}
    data["Math Operators"] = new_math_data
    
    with open('unicode_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print("Consolidated into:")
    for k, v in new_math_data.items():
        print(f" - {k}: {len(v)} chars")

if __name__ == "__main__":
    main()
