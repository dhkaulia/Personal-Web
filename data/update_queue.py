#!/usr/bin/env python3
"""
CLI utility to manage the Mabar Waiting List in data/waiting-list.json.
Usage:
    py data/update_queue.py list
    py data/update_queue.py add "Keyaru" 6 "VIP"
    py data/update_queue.py play "Keyaru" "Freydhite"   <- mark 1+ players as PLAYING
    py data/update_queue.py set "Keyaru" 4
    py data/update_queue.py dec "Keyaru"
    py data/update_queue.py remove "Keyaru"
    py data/update_queue.py clear
"""

import sys
import json
import os
from datetime import datetime

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "waiting-list.json")

def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {QUEUE_FILE}: {e}")
        return []

def save_queue(queue):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    print("Queue successfully saved.")

def list_queue():
    queue = load_queue()
    if not queue:
        print("Queue is empty.")
        return
    print(f"\n--- CURRENT MABAR QUEUE ({len(queue)} players) ---")
    for i, p in enumerate(queue, 1):
        status = p.get('status', 'waiting').upper()
        print(f"#{i:02d} | {p['name']:<12} | {p.get('games', 0)} Game | {p.get('tier', 'VIP')} | {status}")
    print("------------------------------------------\n")

def add_player(name, games, tier="VIP"):
    queue = load_queue()
    tier = tier.upper()
    now_str = datetime.now().strftime("%H:%M WIB")
    
    # Check if player already exists
    for p in queue:
        if p["name"].lower() == name.lower():
            p["games"] = int(games)
            p["tier"] = tier
            print(f"Updated existing player {name}: {games} Game ({tier})")
            save_queue(queue)
            list_queue()
            return
            
    status = "playing" if len(queue) == 0 else ("next" if len(queue) == 1 else "waiting")
    new_entry = {
        "id": str(len(queue) + 1),
        "name": name,
        "games": int(games),
        "tier": tier,
        "status": status,
        "joinedAt": now_str
    }
    queue.append(new_entry)
    print(f"Added {name} to queue: {games} Game ({tier})")
    save_queue(queue)
    list_queue()

def set_games(name, games):
    queue = load_queue()
    found = False
    for p in queue:
        if p["name"].lower() == name.lower():
            p["games"] = int(games)
            found = True
            print(f"Updated {name} to {games} Game")
            break
    if not found:
        print(f"Player {name} not found in queue.")
        return
    save_queue(queue)
    list_queue()

def decrement_games(name):
    queue = load_queue()
    found = False
    for p in queue:
        if p["name"].lower() == name.lower():
            p["games"] = max(0, int(p.get("games", 1)) - 1)
            found = True
            print(f"Decremented {name} to {p['games']} Game remaining")
            if p["games"] == 0:
                print(f"Notice: {name} has completed all games!")
            break
    if not found:
        print(f"Player {name} not found in queue.")
        return
    save_queue(queue)
    list_queue()

def set_playing(names):
    """Mark one or more players as PLAYING; redistribute next/waiting for the rest."""
    queue = load_queue()
    names_lower = [n.lower() for n in names]
    not_found = [n for n in names if n.lower() not in [p["name"].lower() for p in queue]]
    if not_found:
        print(f"Players not found in queue: {', '.join(not_found)}")
        return

    playing_set = set(names_lower)
    bench = [p for p in queue if p["name"].lower() not in playing_set]

    for p in queue:
        if p["name"].lower() in playing_set:
            p["status"] = "playing"
        else:
            idx = bench.index(p)
            p["status"] = "next" if idx == 0 else "waiting"

    save_queue(queue)
    print(f"Now PLAYING: {', '.join(names)}")
    list_queue()

def remove_player(name):
    queue = load_queue()
    initial_len = len(queue)
    queue = [p for p in queue if p["name"].lower() != name.lower()]
    if len(queue) == initial_len:
        print(f"Player {name} not found.")
        return
    # Recalculate status for remaining
    if queue:
        queue[0]["status"] = "playing"
    if len(queue) > 1:
        queue[1]["status"] = "next"
    save_queue(queue)
    print(f"Removed {name} from queue.")
    list_queue()

def clear_queue():
    save_queue([])
    print("Queue cleared.")

def main():
    if len(sys.argv) < 2:
        list_queue()
        print("Usage: py data/update_queue.py [list | add <name> <games> [tier] | play <name1> [name2 ...] | set <name> <games> | dec <name> | remove <name> | clear]")
        return

    cmd = sys.argv[1].lower()
    if cmd == "list":
        list_queue()
    elif cmd == "add":
        if len(sys.argv) < 4:
            print("Usage: py data/update_queue.py add <name> <games> [VIP|SVIP]")
            return
        name = sys.argv[2]
        games = sys.argv[3]
        tier = sys.argv[4] if len(sys.argv) > 4 else "VIP"
        add_player(name, games, tier)
    elif cmd in ("set", "update"):
        if len(sys.argv) < 4:
            print("Usage: py data/update_queue.py set <name> <games>")
            return
        set_games(sys.argv[2], sys.argv[3])
    elif cmd in ("dec", "decrement", "-1"):
        if len(sys.argv) < 3:
            print("Usage: py data/update_queue.py dec <name>")
            return
        decrement_games(sys.argv[2])
    elif cmd in ("remove", "rm", "del"):
        if len(sys.argv) < 3:
            print("Usage: py data/update_queue.py remove <name>")
            return
        remove_player(sys.argv[2])
    elif cmd in ("play", "playing", "setplaying"):
        if len(sys.argv) < 3:
            print("Usage: py data/update_queue.py play <name1> [name2 ...]")
            return
        set_playing(sys.argv[2:])
    elif cmd == "clear":
        clear_queue()
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
