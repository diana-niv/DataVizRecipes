import pandas as pd
import json
import ast
from itertools import combinations
import collections

# ==========================================
# 1. CONFIGURATION
# ==========================================
INPUT_FILE = "your_dataset.csv"
OUTPUT_FILE = "data.json"

# COLUMN MAPPING (Updated based on your input)
COL_RECIPE_NAME = "recipe_title"
COL_CATEGORY = "category"
COL_INGREDIENTS = "ingredients"
COL_STEPS = "directions"  # You called this 'directions', so we map it here

# FILTER SETTINGS
TARGET_CATEGORY = "Breakfast And Brunch"
MAX_RECIPES = 100
MIN_PAIRING_STRENGTH = 2

# ==========================================
# 2. PROCESSING SCRIPT
# ==========================================
try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print(f"Error: Could not find {INPUT_FILE}")
    exit()

# Filter by Category
df = df[df[COL_CATEGORY].astype(str).str.strip() == TARGET_CATEGORY]

if len(df) == 0:
    print("Warning: No recipes found for this category.")
    exit()

# Sample if too large
if len(df) > MAX_RECIPES:
    df = df.sample(n=MAX_RECIPES, random_state=42)

# Function to convert stringified lists "['a','b']" to Python lists
def safe_convert(val):
    try:
        # If it's already a list, return it
        if isinstance(val, list): return val
        # If it's a string looking like a list, convert it
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        # Fallback: if it's a plain string, split by newlines or return empty
        return str(val).split('\n') if isinstance(val, str) else []

# Apply conversion
df[COL_INGREDIENTS] = df[COL_INGREDIENTS].apply(safe_convert)
df[COL_STEPS] = df[COL_STEPS].apply(safe_convert)

# --- Build Ingredient Network ---
ingredient_counts = collections.Counter()
pairings = collections.Counter()

for ingredients in df[COL_INGREDIENTS]:
    # Clean string items
    cleaned_ingredients = [str(i).strip().lower() for i in ingredients]
    ingredient_counts.update(cleaned_ingredients)
    
    unique_ing = sorted(list(set(cleaned_ingredients)))
    for pair in combinations(unique_ing, 2):
        pairings.update([pair])

nodes = []
pantry_items = ['flour', 'sugar', 'salt', 'oil', 'butter', 'baking powder', 'egg', 'milk']
produce_items = ['apple', 'banana', 'spinach', 'carrot', 'onion', 'fruit', 'berry']

for name, count in ingredient_counts.items():
    group = "other"
    if any(p in name for p in pantry_items): group = "pantry"
    elif any(p in name for p in produce_items): group = "produce"
    
    if count >= 2: 
        nodes.append({
            "id": name,
            "name": name.title(),
            "group": group,
            "popularity": count
        })

links = []
valid_node_ids = {n["id"] for n in nodes}

for (source, target), weight in pairings.items():
    if source in valid_node_ids and target in valid_node_ids:
        if weight >= MIN_PAIRING_STRENGTH:
            links.append({
                "source": source,
                "target": target,
                "strength": weight
            })

# --- Build Timeline (Single Recipe) ---
sample_recipe = df.iloc[0]
raw_steps = sample_recipe[COL_STEPS]

timeline_data = []
current_time = 0

for i, step_text in enumerate(raw_steps):
    task_type = "active"
    duration = 10
    
    lower_text = str(step_text).lower()
    # Keyword detection for passive time
    if "bake" in lower_text or "cool" in lower_text or "chill" in lower_text or "simmer" in lower_text:
        task_type = "passive"
        duration = 30
        
    timeline_data.append({
        "step": i + 1,
        "task": str(step_text)[:60] + "...",
        "full_text": str(step_text),
        "type": task_type,
        "start": current_time,
        "duration": duration
    })
    current_time += duration

final_data = {
    "recipe_title": sample_recipe[COL_RECIPE_NAME],
    "ingredients": nodes,
    "links": links,
    "timeline": timeline_data
}

with open(OUTPUT_FILE, 'w') as f:
    json.dump(final_data, f, indent=2)

print(f"Successfully processed {len(df)} recipes.")
print(f"Saved {len(nodes)} ingredients and {len(links)} links to {OUTPUT_FILE}")