#!/usr/bin/env python3
"""
Lightweight Webhook Server for Mabar Waiting List
Zero external dependencies required (uses Python standard library).

Endpoints:
    GET  /api/queue            -> Returns current waiting list (with CORS headers)
    POST /api/queue            -> Updates waiting list via JSON payload
    POST /api/webhook/discord  -> Handles webhook / Discord payload
"""

import http.server
import json
import os
import subprocess
import sys
from datetime import datetime

PORT = int(os.environ.get("PORT", 8080))
QUEUE_FILE = os.path.join(os.path.dirname(__file__), "data", "waiting-list.json")
SECRET_TOKEN = os.environ.get("QUEUE_SECRET_TOKEN", "") # Optional authentication token
AUTO_GIT_PUSH = os.environ.get("AUTO_GIT_PUSH", "false").lower() in ("true", "1")

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
            print("Auto Git Push enabled. Committing and pushing...")
            subprocess.run(["git", "add", QUEUE_FILE], check=True)
            subprocess.run(["git", "commit", "-m", "chore: update waiting list via webhook"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("Git push successful.")
        except Exception as e:
            print(f"Git push failed: {e}")

class QueueWebhookHandler(http.server.BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Secret-Token")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/queue") or self.path == "/":
            data = load_queue()
            encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(encoded)
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

    def do_POST(self):
        if not (self.path.startswith("/api/queue") or self.path.startswith("/api/webhook")):
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')
            return

        # Optional Token Validation
        if SECRET_TOKEN:
            token = self.headers.get("X-Secret-Token") or self.headers.get("Authorization", "").replace("Bearer ", "")
            if token != SECRET_TOKEN:
                self.send_response(401)
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(b'{"error": "Unauthorized: Invalid secret token"}')
                return

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8"))
        except Exception as e:
            self.send_response(400)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {e}"}).encode("utf-8"))
            return

        action = body.get("action", "add").lower()
        name = body.get("name")
        games = body.get("games")
        tier = (body.get("tier") or "VIP").upper()
        now_str = datetime.now().strftime("%H:%M WIB")

        queue = load_queue()
        message = ""

        # Handle Actions
        if action in ("add", "upsert"):
            if not name:
                self._send_bad_request("Field 'name' is required for action 'add'.")
                return
            games = int(games) if games is not None else 1
            
            # Check if player exists
            existing = next((p for p in queue if p["name"].lower() == name.lower()), None)
            if existing:
                existing["games"] = games
                if "tier" in body:
                    existing["tier"] = tier
                message = f"Updated {name}: {games} Game ({existing['tier']})"
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
                message = f"Added {name}: {games} Game ({tier})"

        elif action in ("set", "update"):
            if not name or games is None:
                self._send_bad_request("Fields 'name' and 'games' are required for action 'set'.")
                return
            existing = next((p for p in queue if p["name"].lower() == name.lower()), None)
            if not existing:
                self._send_not_found(f"Player '{name}' not found in queue.")
                return
            existing["games"] = int(games)
            if "tier" in body:
                existing["tier"] = tier
            message = f"Updated {name} to {games} Game"

        elif action in ("decrement", "dec", "-1"):
            if not name:
                self._send_bad_request("Field 'name' is required for action 'decrement'.")
                return
            existing = next((p for p in queue if p["name"].lower() == name.lower()), None)
            if not existing:
                self._send_not_found(f"Player '{name}' not found in queue.")
                return
            existing["games"] = max(0, int(existing.get("games", 1)) - 1)
            message = f"Decremented {name} to {existing['games']} Game remaining"

        elif action in ("remove", "delete"):
            if not name:
                self._send_bad_request("Field 'name' is required for action 'remove'.")
                return
            initial_len = len(queue)
            queue = [p for p in queue if p["name"].lower() != name.lower()]
            if len(queue) == initial_len:
                self._send_not_found(f"Player '{name}' not found.")
                return
            if queue:
                queue[0]["status"] = "playing"
            if len(queue) > 1:
                queue[1]["status"] = "next"
            message = f"Removed {name} from queue"

        elif action == "clear":
            queue = []
            message = "Queue cleared"

        else:
            self._send_bad_request(f"Unknown action: '{action}'. Allowed: add, set, decrement, remove, clear.")
            return

        save_queue(queue)

        response_body = {
            "success": True,
            "message": message,
            "queue": queue
        }
        encoded = json.dumps(response_body, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(encoded)

    def _send_bad_request(self, msg):
        self.send_response(400)
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode("utf-8"))

    def _send_not_found(self, msg):
        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode("utf-8"))

def run():
    server_address = ("", PORT)
    httpd = http.server.HTTPServer(server_address, QueueWebhookHandler)
    print(f"==================================================")
    print(f" Mabar Queue Webhook Server running on port {PORT}")
    print(f" GET  http://localhost:{PORT}/api/queue")
    print(f" POST http://localhost:{PORT}/api/queue")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    run()
