# Mabar Waiting List Setup & Discord Control Guide

This guide explains how to control and update the **Mabar Waiting List** on your website.

---

## 1. How It Works

1. **Frontend Display (`index.html`)**:
   - The waiting list table sits directly below **Quick Links** (`#queue`).
   - Automatically polls `data/waiting-list.json` (or a configured remote API URL) every 20 seconds.
   - Includes real-time indicators, tier styling (`VIP` vs `SVIP`), remaining game counters, empty states, and manual refresh.

2. **Data Source (`data/waiting-list.json`)**:
   - Stores current players, remaining games, and membership tiers:
   ```json
   [
     {
       "id": "1",
       "name": "Keyaru",
       "games": 6,
       "tier": "VIP",
       "status": "playing",
       "joinedAt": "11:30 WIB"
     },
     {
       "id": "2",
       "name": "Freydhite",
       "games": 3,
       "tier": "SVIP",
       "status": "waiting",
       "joinedAt": "12:15 WIB"
     }
   ]
   ```

---

## 2. Option A: Quick CLI (Instant Local Updates)

You can instantly modify the queue right from your terminal without setting up a bot:

```bash
# View current waiting list
py data/update_queue.py list

# Add new player
py data/update_queue.py add "Keyaru" 6 "VIP"
py data/update_queue.py add "Freydhite" 3 "SVIP"

# Change game duration (e.g. from 6 to 4 games)
py data/update_queue.py set "Keyaru" 4
py data/update_queue.py set "Freydhite" 1

# Decrement by 1 game after a match
py data/update_queue.py dec "Keyaru"

# Remove player when done
py data/update_queue.py remove "Keyaru"

# Clear entire list
py data/update_queue.py clear
```

---

## 3. Option B: Webhook Server (`webhook_server.py`)

Run the zero-dependency Python server:
```bash
py webhook_server.py
```

### Webhook API Endpoints:
- `GET http://localhost:8080/api/queue`
- `POST http://localhost:8080/api/queue`

### Webhook Payload Examples:

#### 1. Change Game Duration (e.g., Keyaru to 4 games)
```json
{
  "action": "set",
  "name": "Keyaru",
  "games": 4
}
```

#### 2. Add New Player (with VIP or SVIP)
```json
{
  "action": "add",
  "name": "Freydhite",
  "games": 3,
  "tier": "SVIP"
}
```

#### 3. Decrement 1 Game (after match finishes)
```json
{
  "action": "decrement",
  "name": "Keyaru"
}
```

#### 4. Remove Player
```json
{
  "action": "remove",
  "name": "Keyaru"
}
```

*Tip: Set `AUTO_GIT_PUSH=1` so every webhook call automatically commits and pushes to GitHub Pages!*

---

## 4. Option C: Discord Bot (`discord-bot/bot.py`)

Manage everything directly from your Discord server using chat commands:

### Setup:
1. Install `discord.py`:
   ```bash
   pip install discord.py
   ```
2. Set your bot token:
   ```bash
   # Windows Command Prompt / PowerShell
   set DISCORD_BOT_TOKEN=your_token_here
   py discord-bot/bot.py
   ```

### Discord Commands:
| Command | Example | Description |
|---|---|---|
| `!q list` | `!q list` | Displays the current waiting list embed |
| `!q add` | `!q add Keyaru 6 VIP` | Adds Keyaru with 6 games as VIP |
| `!q set` | `!q set Keyaru 4` | Changes Keyaru's remaining games to 4 |
| `!q dec` | `!q dec Keyaru` | Decrements Keyaru's games by 1 |
| `!q remove` | `!q remove Keyaru` | Removes Keyaru from queue |
| `!q clear` | `!q clear` | Clears all players from queue |

---

## 5. Option D: 100% Serverless (Cloudflare Worker)

If you don't want to run Python on your computer 24/7:
1. Copy `cloudflare-worker/worker.js` to a free Cloudflare Worker.
2. Bind a KV namespace named `QUEUE_KV`.
3. In `index.html`, set:
   ```html
   <script>
     window.QUEUE_API_URL = "https://your-worker.your-subdomain.workers.dev/api/queue";
   </script>
   ```
4. Now you can send webhooks to `https://your-worker.your-subdomain.workers.dev/api/queue` from anywhere (Discord Webhook, Postman, Zapier, Make, etc.)!
