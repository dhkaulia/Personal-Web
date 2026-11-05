#!/usr/bin/env python3
"""
Discord Bot to manage Mabar Waiting List on your website.

Commands available in Discord:
  !q list                     -> Show current waiting list
  !q add <name> <games> [VIP|SVIP] -> Add player to waiting list
  !q set <name> <games>       -> Change remaining games (e.g. !q set Keyaru 4)
  !q dec <name>               -> Decrement game duration by 1 after match
  !q remove <name>            -> Remove player from queue
  !q clear                    -> Clear the entire queue

Slash Commands (Discord 2.0+):
  /queue add player:Keyaru games:6 tier:VIP
  /queue set player:Keyaru games:4
  /queue decrement player:Keyaru
  /queue list
"""

import os
import sys
import json
import subprocess
from datetime import datetime

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("discord.py is not installed. To run the bot, install it via:")
    print("  pip install discord.py")
    sys.exit(1)

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
QUEUE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "waiting-list.json"))
AUTO_GIT_PUSH = os.environ.get("AUTO_GIT_PUSH", "false").lower() in ("true", "1")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=["!q ", "!queue ", "!Q "], intents=intents)

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
    
    if AUTO_GIT_PUSH:
        try:
            repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            subprocess.run(["git", "add", QUEUE_FILE], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "chore: update waiting list via Discord bot"], cwd=repo_dir, check=True)
            subprocess.run(["git", "push"], cwd=repo_dir, check=True)
            print("Auto Git push completed successfully.")
        except Exception as e:
            print(f"Git push failed: {e}")

def create_queue_embed(queue, title="MABAR WAITING LIST"):
    embed = discord.Embed(
        title=f"🎮 {title}",
        color=0x111111,
        timestamp=datetime.now()
    )
    if not queue:
        embed.description = "*Antrean saat ini kosong. Buka Sociabuzz untuk join!*"
        embed.set_footer(text="Juki Akira Hub · Updated Live")
        return embed

    lines = []
    for i, p in enumerate(queue, 1):
        s = p.get("status", "waiting").lower()
        if s == "playing":
            status_icon = "🟢 PLAYING"
        elif s == "next":
            status_icon = "🟡 NEXT"
        else:
            status_icon = "⚪ QUEUE"
        tier_tag = f"**[{p.get('tier', 'VIP').upper()}]**"
        games = f"{p.get('games', 1)} Game"
        lines.append(f"`#{i:02d}` **{p['name']}** — {games} {tier_tag} · *{status_icon}*")

    embed.description = "\n".join(lines)
    embed.set_footer(text=f"Total: {len(queue)} Players · Updated Live")
    return embed

@bot.event
async def on_ready():
    print(f"==================================================")
    print(f" Logged in as: {bot.user.name} ({bot.user.id})")
    print(f" Waiting list target: {QUEUE_FILE}")
    print(f" Auto Git Push: {AUTO_GIT_PUSH}")
    print(f"==================================================")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

# ----- PREFIX COMMANDS -----

@bot.command(name="list", aliases=["show", "status"])
async def cmd_list(ctx):
    queue = load_queue()
    embed = create_queue_embed(queue)
    await ctx.send(embed=embed)

@bot.command(name="add")
async def cmd_add(ctx, name: str, games: int, tier: str = "VIP"):
    queue = load_queue()
    tier = tier.upper()
    now_str = datetime.now().strftime("%H:%M WIB")

    existing = next((p for p in queue if p["name"].lower() == name.lower()), None)
    if existing:
        existing["games"] = games
        existing["tier"] = tier
    else:
        status = "playing" if len(queue) == 0 else ("next" if len(queue) == 1 else "waiting")
        queue.append({
            "id": str(len(queue) + 1),
            "name": name,
            "games": games,
            "tier": tier,
            "status": status,
            "joinedAt": now_str
        })

    save_queue(queue)
    embed = create_queue_embed(queue, title=f"Updated: {name} Added ({games} Game - {tier})")
    await ctx.send(embed=embed)

@bot.command(name="set", aliases=["update"])
async def cmd_set(ctx, name: str, games: int):
    queue = load_queue()
    existing = next((p for p in queue if p["name"].lower() == name.lower()), None)
    if not existing:
        await ctx.send(f"❌ Player `{name}` tidak ditemukan dalam antrean.")
        return

    existing["games"] = int(games)
    save_queue(queue)
    embed = create_queue_embed(queue, title=f"Duration Updated: {name} ({games} Game)")
    await ctx.send(embed=embed)

@bot.command(name="dec", aliases=["decrement", "-1"])
async def cmd_dec(ctx, name: str):
    queue = load_queue()
    existing = next((p for p in queue if p["name"].lower() == name.lower()), None)
    if not existing:
        await ctx.send(f"❌ Player `{name}` tidak ditemukan dalam antrean.")
        return

    existing["games"] = max(0, int(existing.get("games", 1)) - 1)
    save_queue(queue)
    msg = f"Sisa {existing['games']} Game"
    if existing["games"] == 0:
        msg += " (Game selesai! Siap di-remove)"
    embed = create_queue_embed(queue, title=f"Decremented: {name} — {msg}")
    await ctx.send(embed=embed)

@bot.command(name="remove", aliases=["rm", "del"])
async def cmd_remove(ctx, name: str):
    queue = load_queue()
    initial_len = len(queue)
    queue = [p for p in queue if p["name"].lower() != name.lower()]
    if len(queue) == initial_len:
        await ctx.send(f"❌ Player `{name}` tidak ditemukan.")
        return

    # Only reset if no one is currently playing
    currently_playing = [p for p in queue if p.get("status") == "playing"]
    if not currently_playing and queue:
        queue[0]["status"] = "playing"
        if len(queue) > 1:
            queue[1]["status"] = "next"

    save_queue(queue)
    embed = create_queue_embed(queue, title=f"Removed: {name} dari antrean")
    await ctx.send(embed=embed)

@bot.command(name="play", aliases=["playing", "setplaying"])
async def cmd_play(ctx, *names: str):
    """Mark one or more players as PLAYING.
    Usage: !q play Keyaru  OR  !q play Keyaru Freydhite
    """
    if not names:
        await ctx.send("Usage: `!q play <name1> [name2 ...]`")
        return
    queue = load_queue()
    not_found = [n for n in names if not any(p["name"].lower() == n.lower() for p in queue)]
    if not_found:
        await ctx.send(f"❌ Tidak ditemukan: {', '.join(not_found)}")
        return

    playing_set = {n.lower() for n in names}
    bench = [p for p in queue if p["name"].lower() not in playing_set]

    for p in queue:
        if p["name"].lower() in playing_set:
            p["status"] = "playing"
        else:
            idx = bench.index(p)
            p["status"] = "next" if idx == 0 else "waiting"

    save_queue(queue)
    label = ", ".join(names)
    embed = create_queue_embed(queue, title=f"Now PLAYING: {label}")
    await ctx.send(embed=embed)

@bot.command(name="clear")
async def cmd_clear(ctx):
    save_queue([])
    embed = create_queue_embed([], title="Queue Cleared")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable is not set.")
        print("Run the bot with your Discord token:")
        print("  set DISCORD_BOT_TOKEN=your_token_here")
        print("  py discord-bot/bot.py")
        sys.exit(1)
    bot.run(TOKEN)
