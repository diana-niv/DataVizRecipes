import pandas as pd
import json
import re
import ast
import random

INPUT_FILE = "breakfast_recipes.csv"
OUTPUT_FILE = "parsed_data.json"

MAX_RECIPES = 300

COL_TITLE = "recipe_title"
COL_INGREDIENTS = "ingredients"
COL_DIRECTIONS = "directions"
COL_SUBCATEGORY = "subcategory"

def clean_ingredient_name(text):
    text = str(text).lower().strip()
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'[^a-z\s-]', '', text)
    
    STOP_WORDS = {
        'cup', 'cups', 'tsp', 'tbsp', 'teaspoon', 'tablespoon', 'oz', 'ounce', 
        'gram', 'g', 'lb', 'pound', 'liter', 'quart', 'pint', 'gallon',
        'can', 'cans', 'package', 'packages', 'pack', 'container', 'box', 'bag', 
        'bottle', 'jar', 'envelope', 'stick', 'sticks', 'bar', 'bars', 'link', 'links',
        'slice', 'slices', 'clove', 'cloves', 'pinch', 'dash', 'drop', 'drops',
        'head', 'bunch', 'stalk', 'sprig', 'fillet', 'filet', 'piece', 'pieces',
        'chopped', 'diced', 'minced', 'sliced', 'peeled', 'crushed', 'beaten', 
        'softened', 'melted', 'thawed', 'frozen', 'shredded', 'grated', 'toasted',
        'roasted', 'baked', 'cooked', 'uncooked', 'boiled', 'fried', 'grilled',
        'steamed', 'smoked', 'cured', 'dried', 'fresh', 'warm', 'cold', 'hot',
        'room', 'temperature', 'cut', 'into', 'cubes', 'chunks', 'wedges', 'rings',
        'halved', 'quartered', 'cored', 'sifted', 'divided', 'separated', 'drained',
        'rinsed', 'pitted', 'trimmed', 'cleaned', 'rubbed', 'crumbled', 'mash', 'mashed',
        'large', 'small', 'medium', 'jumbo', 'whole', 'lean', 'extra', 'virgin',
        'all-purpose', 'purpose', 'self-rising', 'rising', 'active', 'dry', 'instant',
        'white', 'brown', 'red', 'green', 'yellow', 'blue', 'black', 'orange',
        'sweet', 'sour', 'spicy', 'unsalted', 'salted', 'kosher', 'sea', 'coarse',
        'fine', 'granulated', 'powdered', 'confectioners', 'packed', 'firm', 'soft',
        'ripe', 'boneless', 'skinless', 'fat-free', 'low-fat', 'condensed', 'evaporated',
        'heavy', 'whipping', 'double', 'single', 'distilled', 'boiling',
        'and', 'or', 'of', 'to', 'for', 'with', 'in', 'as', 'needed', 'taste', 
        'optional', 'garnish', 'about', 'more', 'less', 'plus'
    }

    words = text.split()
    cleaned_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    result = " ".join(cleaned_words).strip()
    
    if "flour" in result: return "flour"
    if "sugar" in result and "brown" not in result: return "sugar"
    if "butter" in result and "peanut" not in result: return "butter"
    if "egg" in result and "plant" not in result: return "egg"
    if "milk" in result and "coconut" not in result and "almond" not in result: return "milk"
    if "sausage" in result: return "sausage"
    if "bacon" in result: return "bacon"
    if "cheese" in result: return "cheese"

    return result

def parse_instruction_step(step_text):
    text = str(step_text).lower()
    duration = 10 
    match = re.search(r'(\d+)\s*(min|hr|hour)', text)
    if match:
        number = int(match.group(1))
        if 'h' in match.group(2): duration = number * 60
        else: duration = number
    passive_keywords = ['bake', 'cool', 'chill', 'simmer', 'rise', 'wait', 'roast', 'marinate', 'rest']
    task_type = "passive" if any(word in text for word in passive_keywords) else "active"
    return {"task_text": step_text, "duration": duration, "type": task_type}

def safe_parse_list(val):
    try:
        if isinstance(val, list): return val
        if pd.isna(val) or val == "": return []
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return str(val).split('\n')

print(f"Reading {INPUT_FILE}...")
try:
    df = pd.read_csv(INPUT_FILE, sep=';', on_bad_lines='skip', skipinitialspace=True, engine='python')
except FileNotFoundError:
    print(f"Error: Could not find {INPUT_FILE}")
    exit()

df.columns = df.columns.str.strip().str.lower()
final_data = []

print(f"Processing {len(df)} recipes...")

for index, row in df.iterrows():
    raw_ing_list = safe_parse_list(row[COL_INGREDIENTS])
    clean_ingredients = []
    
    for item in raw_ing_list:
        clean_name = clean_ingredient_name(item)
        if clean_name and len(clean_name) > 1: 
            if clean_name not in clean_ingredients:
                clean_ingredients.append(clean_name)
    
    raw_dir_list = safe_parse_list(row[COL_DIRECTIONS])
    timeline_steps = []
    current_time_marker = 0
    for i, step in enumerate(raw_dir_list):
        step_info = parse_instruction_step(step)
        step_info["step_number"] = i + 1
        step_info["start_time"] = current_time_marker
        timeline_steps.append(step_info)
        current_time_marker += step_info["duration"]

    subcat = str(row[COL_SUBCATEGORY]).strip()
    if subcat == "Breakfast Burritos": subcat = "Burritos"
    elif subcat == "Southern Breakfast And Brunch": subcat = "Southern"
    elif subcat == "Breakfast Bowls": subcat = "Bowls"
    elif subcat == "Breakfast Casseroles": subcat = "Casseroles"
    elif subcat == "Breakfast Potatoes": subcat = "Potatoes"
    elif subcat == "Breakfast Cookies": subcat = "Cookies"
    elif subcat == "Breakfast Quiche": subcat = "Quiche"
    elif subcat == "Breakfast Bread": subcat = "Bread"
    elif subcat == "Breakfast Meat And Seafood": subcat = "Meat And Seafood"
    elif subcat == "Breakfast Sausage": subcat = "Sausage"
    elif subcat == "Healthy Breakfast And Brunch": subcat = "Healthy"
    elif subcat == "Breakfast Bacon": subcat = "Bacon"
    elif subcat == "Breakfast Eggs": subcat = "Eggs"

    final_data.append({
        "id": index,
        "title": row[COL_TITLE],
        "subcategory": subcat,
        "ingredients": clean_ingredients,
        "timeline": timeline_steps,
        "total_time": current_time_marker
    })

if len(final_data) > MAX_RECIPES:
    print(f"Reducing dataset from {len(final_data)} to {MAX_RECIPES} random recipes...")
    random.seed(42) 
    final_data = random.sample(final_data, MAX_RECIPES)

with open(OUTPUT_FILE, 'w') as f:
    json.dump(final_data, f, indent=2)

print(f"Success! Saved {len(final_data)} recipes to {OUTPUT_FILE}")