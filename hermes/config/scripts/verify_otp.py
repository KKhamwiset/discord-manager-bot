#!/usr/bin/env python3
"""
Mochi Host OTP Verification Service
Verifies 6-digit TOTP (RFC 6238) to unlock remote command execution on host machine (mypc).
"""

import sys
import os
import time
import json
import hmac
import hashlib
import struct
import base64
from pathlib import Path

SESSION_FILE = Path(os.environ.get("HOST_OTP_SESSION_FILE", "/tmp/host_otp_session.json"))
SESSION_TTL_SECONDS = int(os.environ.get("HOST_OTP_TTL", 1800))  # 30 minutes default
DEFAULT_SECRET = "4UNGXTOTY3FHZ45MIKOP7HSBUJS73WGQ"

def get_secret() -> str:
    secret = os.environ.get("HOST_TOTP_SECRET", "").strip()
    if secret:
        return secret
    
    # Try reading from .totp_secret or .env
    for candidate in [Path("/data/hermes/.totp_secret"), Path.home() / ".hermes" / ".totp_secret", Path(".totp_secret")]:
        if candidate.exists():
            try:
                s = candidate.read_text().strip()
                if s:
                    return s
            except Exception:
                pass
    return DEFAULT_SECRET

def compute_totp(secret: str, counter: int, digits: int = 6) -> str:
    key = base64.b32decode(secret.upper(), casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return f"{code:0{digits}d}"

def verify_code(secret: str, input_code: str, window: int = 1) -> bool:
    input_code = str(input_code).strip()
    if len(input_code) != 6 or not input_code.isdigit():
        return False
    
    now = int(time.time())
    step = now // 30
    
    for offset in range(-window, window + 1):
        expected = compute_totp(secret, step + offset)
        if hmac.compare_digest(expected, input_code):
            return True
    return False

def check_status() -> dict:
    if not SESSION_FILE.exists():
        return {"unlocked": False, "remaining_seconds": 0, "message": "Host session is locked."}
    
    try:
        data = json.loads(SESSION_FILE.read_text())
        now = time.time()
        expires_at = data.get("expires_at", 0)
        if now < expires_at:
            rem = int(expires_at - now)
            return {
                "unlocked": True,
                "remaining_seconds": rem,
                "message": f"Host session is unlocked ({rem} seconds remaining)."
            }
        else:
            SESSION_FILE.unlink(missing_ok=True)
            return {"unlocked": False, "remaining_seconds": 0, "message": "Host session expired."}
    except Exception as exc:
        SESSION_FILE.unlink(missing_ok=True)
        return {"unlocked": False, "remaining_seconds": 0, "message": f"Session error: {exc}"}

def unlock_session(ttl_seconds: int = SESSION_TTL_SECONDS) -> dict:
    now = time.time()
    expires_at = now + ttl_seconds
    data = {
        "unlocked_at": now,
        "expires_at": expires_at,
        "ttl": ttl_seconds
    }
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data))
    return {
        "status": "ok",
        "unlocked": True,
        "expires_at": expires_at,
        "remaining_seconds": ttl_seconds,
        "message": f"Host connection unlocked successfully for {ttl_seconds // 60} minutes."
    }

def lock_session() -> dict:
    SESSION_FILE.unlink(missing_ok=True)
    return {"status": "ok", "unlocked": False, "message": "Host connection locked."}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: verify_otp.py <6-digit-otp> | --status | --lock | --current"}))
        sys.exit(1)

    arg = sys.argv[1].strip()
    secret = get_secret()

    if arg == "--status":
        res = check_status()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("unlocked") else 1)
    
    elif arg == "--lock":
        res = lock_session()
        print(json.dumps(res, indent=2))
        sys.exit(0)

    elif arg == "--current":
        # Internal test / debug
        now_code = compute_totp(secret, int(time.time() // 30))
        print(json.dumps({"current_code": now_code}))
        sys.exit(0)

    else:
        # Treat argument as OTP code
        if verify_code(secret, arg):
            res = unlock_session()
            print(json.dumps(res, indent=2))
            sys.exit(0)
        else:
            print(json.dumps({
                "status": "error",
                "unlocked": False,
                "message": "Invalid or expired OTP code. Please check your authenticator or run get-otp.ps1 on host machine."
            }, indent=2))
            sys.exit(2)

if __name__ == "__main__":
    main()
