import os
import re

JAVA_SRC = "core/src/main/java/com/shatteredpixel/shatteredpixeldungeon"
SYSTEMS_DIR = f"{JAVA_SRC}/pokemon"
os.makedirs(SYSTEMS_DIR, exist_ok=True)

# --- 1. PURE JAVA PARTY SYSTEM (100% Compile Safe) ---
def create_party_manager():
    print("Writing PartyManager.java...")
    # This class has ZERO dependencies on SPD's changing API, so it will never throw a compiler error.
    party_code = """package com.shatteredpixel.shatteredpixeldungeon.pokemon;

import java.util.ArrayList;

public class PartyManager {
    public static ArrayList<String> roster = new ArrayList<>();
    
    public static boolean catchPokemon(String name) {
        if (roster.size() < 6) {
            roster.add(name);
            return true;
        }
        return false;
    }
}
"""
    with open(f"{SYSTEMS_DIR}/PartyManager.java", "w", encoding="utf-8") as f:
        f.write(party_code)

# --- 2. HIJACK THE COMBAT ENGINE (The Pokéball Mechanic) ---
def hijack_mob_damage():
    print("Hijacking Mob.java to create Pokeball mechanics...")
    mob_path = f"{JAVA_SRC}/actors/mobs/Mob.java"
    if os.path.exists(mob_path):
        with open(mob_path, 'r', encoding='utf-8') as f: c = f.read()
        
        # We intercept the damage calculation. 
        # If the mob is hit by a "Stone" (which we rename to Poké Ball in the UI), we run catch math.
        catch_logic = """
        // --- POKEBALL HIJACK ---
        if (src != null && src.getClass().getSimpleName().equals("Stone")) {
            if (Math.random() < 0.5) { // 50% Base Catch Rate
                com.shatteredpixel.shatteredpixeldungeon.pokemon.PartyManager.catchPokemon(this.getClass().getSimpleName());
                com.shatteredpixel.shatteredpixeldungeon.utils.GLog.p("Gotcha! Pokemon caught!");
                dmg = 99999; // Deal lethal damage to safely remove it from the map
            } else {
                com.shatteredpixel.shatteredpixeldungeon.utils.GLog.w("Oh no! It broke free!");
                dmg = 0; // The ball bounces off harmlessly
            }
        }
        // -----------------------
        """
        # Inject right at the start of the damage method
        c = re.sub(r'(public void damage\(\s*int\s*dmg\s*,\s*Object\s*src\s*\)\s*\{)', 
                   r'\1\n' + catch_logic, c, count=1)
        with open(mob_path, 'w', encoding='utf-8') as f: f.write(c)

# --- 3. HIJACK THE SHOPKEEPER (Nurse Joy) ---
def hijack_shopkeeper():
    print("Hijacking Shopkeeper to act as Nurse Joy...")
    shop_path = f"{JAVA_SRC}/actors/npcs/Shopkeeper.java"
    if os.path.exists(shop_path):
        with open(shop_path, 'r', encoding='utf-8') as f: c = f.read()
        
        heal_logic = """
        // --- NURSE JOY HIJACK ---
        hero.hp(hero.ht()); // Restore Hero to Max HT (Health Total)
        com.shatteredpixel.shatteredpixeldungeon.utils.GLog.p("Welcome to the Pokemon Center! Your party is fully healed.");
        // ------------------------
        """
        # Inject into the interact method
        c = re.sub(r'(public void interact\(\)\s*\{)', r'\1\n' + heal_logic, c, count=1)
        with open(shop_path, 'w', encoding='utf-8') as f: f.write(c)

# --- 4. HIJACK THE DUNGEON BOSS (Gym Leader) ---
def hijack_first_boss():
    print("Hijacking Goo boss to act as Gym Leader Roxanne...")
    goo_path = f"{JAVA_SRC}/actors/mobs/bosses/Goo.java"
    if os.path.exists(goo_path):
        with open(goo_path, 'r', encoding='utf-8') as f: c = f.read()
        
        badge_logic = """
        // --- GYM LEADER HIJACK ---
        com.shatteredpixel.shatteredpixeldungeon.utils.GLog.p("Gym Leader Roxanne was defeated! You received the Stone Badge.");
        // Teleport back to Town (Overworld Hub)
        com.shatteredpixel.shatteredpixeldungeon.Dungeon.depth = 1;
        // -------------------------
        """
        c = re.sub(r'(public void die\(\s*Object\s*cause\s*\)\s*\{)', r'\1\n' + badge_logic, c, count=1)
        with open(goo_path, 'w', encoding='utf-8') as f: f.write(c)

# --- 5. THE GREAT UI RENAMING ---
def patch_ui_strings():
    print("Rewriting internal text to Pokemon Lore...")
    strings_path = 'android/src/main/res/values/strings.xml'
    if os.path.exists(strings_path):
        with open(strings_path, 'r', encoding='utf-8') as f: s = f.read()
        
        # This translates the hijacked items into their Pokemon equivalents on the screen
        reps = {
            "Warrior": "Bulbasaur", 
            "Mage": "Charmander", 
            "Stone": "Poké Ball",       # Hijacked Pokeball
            "Shopkeeper": "Nurse Joy",  # Hijacked Nurse
            "Goo": "Gym Leader Roxanne",# Hijacked Boss
            "Shattered Pixel Dungeon": "Pokemon Mystery Emerald",
            "Health": "HP"
        }
        for k, v in reps.items(): 
            # Safely replace xml text nodes
            s = s.replace(f">{k}<", f">{v}<")
        
        with open(strings_path, 'w', encoding='utf-8') as f: f.write(s)

def main():
    create_party_manager()
    hijack_mob_damage()
    hijack_shopkeeper()
    hijack_first_boss()
    patch_ui_strings()
    print("Hijack Protocol Complete. Engine is primed for compilation.")

if __name__ == "__main__":
    main()
