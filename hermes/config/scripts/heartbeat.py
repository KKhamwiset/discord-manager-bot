#!/usr/bin/env python3
"""Mochi Heartbeat — sends liveness ping to Discord thread"""
import os
import re
import json
import urllib.request
import subprocess
from datetime import datetime


def is_gateway_running() -> bool:
    """Return True only when the Hermes gateway process is actually alive."""
    if os.getenv("HEARTBEAT_REQUIRE_GATEWAY", "1").lower() in {"0", "false", "no", "off"}:
        return True

    try:
        result = subprocess.run(
            ["hermes", "gateway", "status"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        output = f"{result.stdout}\n{result.stderr}"
        return "running" in output.lower() or "active" in output.lower()
    except Exception:
        # Fallback check process list
        try:
            ps_res = subprocess.run(
                ["pgrep", "-f", "hermes gateway"],
                capture_output=True,
                check=False,
            )
            return ps_res.returncode == 0
        except Exception:
            return True


if not is_gateway_running():
    exit(0)

# 1. First check environment variable directly
token = os.getenv("DISCORD_BOT_TOKEN")

# 2. Fallback to reading from ~/.hermes/.env
if not token or "..." in token:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                m = re.match(r'DISCORD_BOT_TOKEN=(.*)', line.strip())
                if m:
                    token = m.group(1).strip()
                    break

if not token or "..." in token:
    print("[SILENT] No valid bot token")
    exit(0)

# Current time
now = datetime.now()
time_str = now.strftime('%H:%M')

CHANNEL_ID = os.getenv("HEARTBEAT_CHANNEL_ID", "1514163672857972757")
payload = json.dumps({"content": f"💓 Hermes heartbeat — {time_str} TST"}).encode('utf-8')

req = urllib.request.Request(
    f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages",
    data=payload,
    headers={
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot/1.0"
    }
)

try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    print(f"OK: {data.get('id', '?')}")
except Exception as e:
    print(f"[SILENT] {e}")
