#!/usr/bin/env python3
"""
One-time setup: creates a public GitHub Gist for the waiting list JSON,
then patches index.html and bot.py to use it.

Run once:
    set GITHUB_TOKEN=your_token_here
    py setup_gist.py
"""
import os, json, sys, urllib.request, urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    print("ERROR: Set GITHUB_TOKEN first.")
    print("  Windows PowerShell: $env:GITHUB_TOKEN='ghp_yourtoken'")
    print("  Then re-run: py setup_gist.py")
    sys.exit(1)

QUEUE_FILE = os.path.join("data", "waiting-list.json")
queue_content = open(QUEUE_FILE, "r", encoding="utf-8").read()

# --- Create the Gist ---
print("Creating public GitHub Gist...")
payload = json.dumps({
    "description": "Juki Akira - Mabar Waiting List (live data)",
    "public": True,
    "files": {
        "waiting-list.json": {"content": queue_content}
    }
}).encode()

req = urllib.request.Request(
    "https://api.github.com/gists",
    data=payload,
    headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "juki-akira-bot"
    },
    method="POST"
)
try:
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
except urllib.error.HTTPError as e:
    print(f"GitHub API error {e.code}: {e.read().decode()}")
    sys.exit(1)

gist_id  = data["id"]
raw_url  = data["files"]["waiting-list.json"]["raw_url"]
# Strip the commit hash from raw URL to get the always-current URL
stable_url = f"https://gist.githubusercontent.com/{data['owner']['login']}/{gist_id}/raw/waiting-list.json"

print(f"\nGist created!")
print(f"  ID       : {gist_id}")
print(f"  Raw URL  : {stable_url}")

# --- Patch index.html ---
html_path = "index.html"
html = open(html_path, "r", encoding="utf-8").read()

old = "      const QUEUE_DATA_URL = window.QUEUE_API_URL || 'data/waiting-list.json';"
new = f"      const QUEUE_DATA_URL = window.QUEUE_API_URL || '{stable_url}';"

if old in html:
    html = html.replace(old, new, 1)
    open(html_path, "w", encoding="utf-8").write(html)
    print(f"\nindex.html patched — now fetching from Gist.")
else:
    print("\nWARNING: Could not auto-patch index.html. Set QUEUE_DATA_URL manually to:")
    print(f"  {stable_url}")

# --- Write .env.bot with the Gist ID so bot.py can read it ---
env_path = "discord-bot/.env.gist"
with open(env_path, "w") as f:
    f.write(f"GIST_ID={gist_id}\n")
    f.write(f"GIST_OWNER={data['owner']['login']}\n")
print(f"\n{env_path} written with GIST_ID and GIST_OWNER.")
print("\nNext: set GITHUB_TOKEN as a permanent env var, then restart the bot.")
print("The bot will now push to the Gist after every queue change — no Netlify deploy lag.")
