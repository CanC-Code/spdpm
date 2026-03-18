import os
import re

JAVA_SRC = "core/src/main/java/com/shatteredpixel/shatteredpixeldungeon"
ITEMS_DIR = f"{JAVA_SRC}/items"
NPCS_DIR = f"{JAVA_SRC}/actors/npcs"
MOBS_DIR = f"{JAVA_SRC}/actors/mobs"
LEVELS_DIR = f"{JAVA_SRC}/levels"
SYSTEMS_DIR = f"{JAVA_SRC}/pokemon" # Brand new directory for our core logic

for directory in [ITEMS_DIR, NPCS_DIR, MOBS_DIR, LEVELS_DIR, SYSTEMS_DIR]:
    os.makedirs(directory, exist_ok=True)

# --- 1. INJECT THE PARTY SYSTEM (Global State) ---
def inject_party_system():
    print("Writing PartyManager.java...")
    party_code = """package com.shatteredpixel.shatteredpixeldungeon.pokemon;

import java.util.ArrayList;

public class PartyManager {
    // Stores the names/IDs of caught Pokemon. Max size 6.
    public static ArrayList<String> roster = new ArrayList<>();
    public static int activeIndex = 0;

    public static boolean catchPokemon(String name) {
        if (roster.size() < 6) {
            roster.add(name);
            return true;
        }
        // In the future: Send to PC Box
        return false;
    }

    public static String getActivePokemon() {
        if (roster.isEmpty()) return "Bulbasaur"; // Fallback starter
        return roster.get(activeIndex);
    }
    
    public static void healParty() {
        // Logic to restore HP/PP for all roster members goes here
    }
}
"""
    with open(f"{SYSTEMS_DIR}/PartyManager.java", "w", encoding="utf-8") as f:
        f.write(party_code)

# --- 2. INJECT THE ADVANCED POKEBALL ---
def inject_pokeball():
    print("Writing PokeBall.java mechanics...")
    pokeball_code = """package com.shatteredpixel.shatteredpixeldungeon.items;

import com.shatteredpixel.shatteredpixeldungeon.actors.Char;
import com.shatteredpixel.shatteredpixeldungeon.actors.mobs.Mob;
import com.shatteredpixel.shatteredpixeldungeon.items.weapon.missiles.MissileWeapon;
import com.shatteredpixel.shatteredpixeldungeon.pokemon.PartyManager;

public class PokeBall extends MissileWeapon {
    
    public PokeBall() {
        super();
        name = "Poké Ball";
        image = 100; // Placeholder for the Pokeball sprite index
    }

    @Override
    public void onThrow(Char cellTarget) {
        if (cellTarget instanceof Mob) {
            Mob wildPokemon = (Mob) cellTarget;
            float catchChance = ((3 * wildPokemon.HT - 2 * wildPokemon.HP) / (3 * wildPokemon.HT)) * 0.5f;
            
            if (com.watabou.utils.Random.Float() < catchChance) {
                String pkmName = wildPokemon.getClass().getSimpleName();
                if (PartyManager.catchPokemon(pkmName)) {
                    wildPokemon.destroy(); // Remove from map
                    com.shatteredpixel.shatteredpixeldungeon.ShatteredPixelDungeon.scene().addMessage("Gotcha! " + pkmName + " was caught!");
                } else {
                    com.shatteredpixel.shatteredpixeldungeon.ShatteredPixelDungeon.scene().addMessage("Your party is full! (PC Box coming soon)");
                }
            } else {
                com.shatteredpixel.shatteredpixeldungeon.ShatteredPixelDungeon.scene().addMessage("Oh no! The Pokemon broke free!");
            }
        }
    }
}
"""
    with open(f"{ITEMS_DIR}/PokeBall.java", "w", encoding="utf-8") as f:
        f.write(pokeball_code)

# --- 3. INJECT THE POKECENTER NURSE ---
def inject_nurse_joy():
    print("Writing NurseJoy.java NPC...")
    nurse_code = """package com.shatteredpixel.shatteredpixeldungeon.actors.npcs;

import com.shatteredpixel.shatteredpixeldungeon.actors.hero.Hero;
import com.shatteredpixel.shatteredpixeldungeon.scenes.GameScene;
import com.shatteredpixel.shatteredpixeldungeon.pokemon.PartyManager;

public class NurseJoy extends NPC {
    
    public NurseJoy() {
        name = "Nurse";
        spriteClass = com.shatteredpixel.shatteredpixeldungeon.sprites.GhostSprite.class; 
    }

    @Override
    public void interact(Hero hero) {
        hero.HP = hero.HT; // Heal active character
        PartyManager.healParty(); // Heal background party
        GameScene.show(new com.shatteredpixel.shatteredpixeldungeon.windows.WndMessage("Welcome to the Pokemon Center! Your party is fully healed."));
    }
}
"""
    with open(f"{NPCS_DIR}/NurseJoy.java", "w", encoding="utf-8") as f:
        f.write(nurse_code)

# --- 4. INJECT GYM LEADER FRAMEWORK ---
def inject_gym_leader():
    print("Writing GymLeader.java Boss framework...")
    gym_code = """package com.shatteredpixel.shatteredpixeldungeon.actors.mobs;

public class GymLeader extends Boss {
    
    public String badgeName;
    
    public GymLeader() {
        super();
        name = "Gym Leader Roxanne";
        HT = HP = 150; // High health for a boss
        defenseSkill = 10;
        badgeName = "Stone Badge";
    }

    @Override
    public void die(Object cause) {
        super.die(cause);
        com.shatteredpixel.shatteredpixeldungeon.ShatteredPixelDungeon.scene().addMessage("You received the " + badgeName + "!");
        // Drop a TM or special item here
    }
}
"""
    with open(f"{MOBS_DIR}/GymLeader.java", "w", encoding="utf-8") as f:
        f.write(gym_code)

# --- 5. INJECT OVERWORLD ROUTING (Dungeon.java) ---
def inject_overworld_routing():
    print("Patching Dungeon Depth Routing...")
    dungeon_path = f"{JAVA_SRC}/Dungeon.java"
    if os.path.exists(dungeon_path):
        with open(dungeon_path, 'r', encoding='utf-8') as f: c = f.read()
        
        routing_logic = """
        public static void descend(int specificDepth) {
            // Depth 1 is Overworld Hub. 
            if (depth == 1 && specificDepth == 10) { depth = 10; } // Enter Granite Cave
            else if (depth == 1 && specificDepth == 20) { depth = 20; } // Enter Meteor Falls
            else if (depth == 15 || depth == 25) { depth = 1; } // Return from Gym
            else { depth++; } 
            
            level = null;
            saveAll();
        }
        """
        c = re.sub(r'public static void descend\(.*?\)\s*\{', routing_logic + "\n    public static void oldDescend() {", c, count=1)
        with open(dungeon_path, 'w', encoding='utf-8') as f: f.write(c)

def run_system_injections():
    inject_party_system()
    inject_pokeball()
    inject_nurse_joy()
    inject_gym_leader()
    inject_overworld_routing()
    print("Pokemon Core Systems successfully injected into the Java source.")

if __name__ == "__main__":
    run_system_injections()
