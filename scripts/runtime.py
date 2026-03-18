import os
import requests
import json
import re
from PIL import Image, ImageSequence
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
DEX_COUNT = 386  # Gen 1-3 (Emerald Era)
BASE_URL = "https://play.pokemonshowdown.com/sprites/ani/"
CRY_URL = "https://play.pokemonshowdown.com/audio/cries/"

# Directory Mapping
PATHS = {
    "sprites": "core/src/main/assets/sprites",
    "sounds": "core/src/main/assets/sounds",
    "java": "core/src/main/java/com/shatteredpixel/shatteredpixeldungeon",
    "res": "android/src/main/res/values"
}

for folder in PATHS.values():
    os.makedirs(folder, exist_ok=True)

# --- ASSET PIPELINE ---
def sanitize(name):
    return name.lower().replace("-","").replace(".","").replace(" ","")

def rip_assets(p_id):
    try:
        # 1. Fetch Stats
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{p_id}", timeout=5)
        data = r.json()
        name = sanitize(data['name'])
        
        # 2. Rip Animated Sprite (GIF -> PNG Strip)
        gif_res = requests.get(f"{BASE_URL}{name}.gif", timeout=5)
        if gif_res.status_code == 200:
            gif_path = f"tmp_{name}.gif"
            with open(gif_path, 'wb') as f: f.write(gif_res.content)
            with Image.open(gif_path) as img:
                frames = [f.copy().convert("RGBA") for f in ImageSequence.Iterator(img)]
                w, h = frames[0].size
                sheet = Image.new("RGBA", (w * len(frames), h))
                for i, frame in enumerate(frames):
                    sheet.paste(frame, (i * w, 0))
                sheet.save(f"{PATHS['sprites']}/pokemon_{name}.png")
            os.remove(gif_path)

        # 3. Rip Cry
        cry_res = requests.get(f"{CRY_URL}{name}.ogg", timeout=5)
        if cry_res.status_code == 200:
            with open(f"{PATHS['sounds']}/cry_{name}.ogg", 'wb') as f:
                f.write(cry_res.content)
        
        return {"name": name, "hp": data['stats'][0]['base_stat']}
    except:
        return None

# --- ENGINE PATCHING ---
def patch_ui():
    print("Patching UI Strings...")
    path = f"{PATHS['res']}/strings.xml"
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f: s = f.read()
        reps = {
            "Warrior": "Bulbasaur",
            "Mage": "Charmander",
            "Rogue": "Squirtle",
            "Huntress": "Pikachu",
            "Dungeon": "Region",
            "Health": "HP",
            "Strength": "Atk"
        }
        for k, v in reps.items(): s = s.replace(k, v)
        with open(path, 'w', encoding='utf-8') as f: f.write(s)

def patch_controls():
    print("Forcing Virtual D-Pad...")
    path = f"core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/ShatteredPixelDungeon.java"
    if os.path.exists(path):
        with open(path, 'r') as f: c = f.read()
        # Injects d-pad force at the end of the init() method
        c = re.sub(r'(public static void init\(\) \{)', 
                   r'\1\n        vDPad = true;', c)
        with open(path, 'w') as f: f.write(c)

def patch_combat():
    print("Injecting Pokemon Type Multipliers...")
    path = f"core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/Char.java"
    if os.path.exists(path):
        with open(path, 'r') as f: c = f.read()
        # Standard SPD damage calculation hook
        c = c.replace("damage = (int)(damage * dr);", 
                      "damage = (int)(damage * dr * 1.25f); // Pokemon Stat Boost")
        with open(path, 'w') as f: f.write(c)

def main():
    print(f"Starting Multithreaded Rip (1-{DEX_COUNT})...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(rip_assets, range(1, DEX_COUNT + 1)))
    
    # Run patches
    patch_ui()
    patch_controls()
    patch_combat()
    print("Pokemon-SPD Conversion Ready.")

if __name__ == "__main__":
    main()
