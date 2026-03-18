import os, requests, json, re
from PIL import Image, ImageSequence
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
DEX_COUNT = 386  # Emerald Era
BASE_URL = "https://play.pokemonshowdown.com/sprites/ani/"
CRY_URL = "https://play.pokemonshowdown.com/audio/cries/"

# Ensure SPD directories exist for injection
folders = [
    "core/src/main/assets/sprites",
    "core/src/main/assets/sounds",
    "core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/pokemon"
]
for f in folders: os.makedirs(f, exist_ok=True)

def sanitize_name(name):
    return name.lower().replace(" ", "").replace("-", "").replace(".", "")

# --- MULTITHREADED ASSET PIPELINE ---
def process_pokemon(p_id):
    try:
        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{p_id}", timeout=10)
        data = resp.json()
        name = sanitize_name(data['name'])
        
        # 1. Sprite Conversion (GIF -> PNG Strip)
        gif_res = requests.get(f"{BASE_URL}{name}.gif", timeout=10)
        if gif_res.status_code == 200:
            temp_gif = f"temp_{name}.gif"
            with open(temp_gif, 'wb') as f: f.write(gif_res.content)
            with Image.open(temp_gif) as img:
                frames = [f.copy().convert("RGBA") for f in ImageSequence.Iterator(img)]
                w, h = frames[0].size
                sheet = Image.new("RGBA", (w * len(frames), h))
                for i, frame in enumerate(frames): sheet.paste(frame, (i * w, 0))
                sheet.save(f"core/src/main/assets/sprites/pokemon_{name}.png")
            os.remove(temp_gif)
        
        # 2. Audio Injection
        cry_res = requests.get(f"{CRY_URL}{name}.ogg", timeout=10)
        if cry_res.status_code == 200:
            with open(f"core/src/main/assets/sounds/cry_{name}.ogg", 'wb') as f:
                f.write(cry_res.content)
        
        return name
    except: return None

# --- ENGINE PATCHES ---
def apply_java_patches():
    # 1. Force Virtual D-Pad (Emerald Controls)
    main_java = 'core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/ShatteredPixelDungeon.java'
    if os.path.exists(main_java):
        with open(main_java, 'r') as f: c = f.read()
        c = c.replace("public static void init() {", 
                      "public static void init() {\n        vDPad = true; // Forced Emerald Controls")
        with open(main_java, 'w') as f: f.write(c)

    # 2. Map Warrior to Bulbasaur Sprite
    hero_sprite = 'core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/sprites/HeroSprite.java'
    if os.path.exists(hero_sprite):
        with open(hero_sprite, 'r') as f: c = f.read()
        # Surgical replacement of the Warrior's texture
        c = c.replace('texture = assets.get( HeroClass.WARRIOR );', 
                      'texture = "sprites/pokemon_bulbasaur.png";')
        with open(hero_sprite, 'w') as f: f.write(c)

    # 3. UI Redesign (Strings)
    strings = 'android/src/main/res/values/strings.xml'
    if os.path.exists(strings):
        with open(strings, 'r') as f: s = f.read()
        reps = {
            "Warrior": "Bulbasaur", "Mage": "Charmander", 
            "Rogue": "Squirtle", "Huntress": "Pikachu",
            "Shattered Pixel Dungeon": "Pokemon Emerald Dungeon",
            "Health": "HP", "Gold": "Pokedollars"
        }
        for old, new in reps.items(): s = s.replace(f">{old}<", f">{new}<")
        with open(strings, 'w') as f: f.write(s)

if __name__ == "__main__":
    print("Starting Emerald Runtime Patcher...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(process_pokemon, range(1, DEX_COUNT + 1))
    
    apply_java_patches()
    print("Mod Injection Successful.")
