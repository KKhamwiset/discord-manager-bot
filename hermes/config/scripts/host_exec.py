#!/usr/bin/env python3
"""
Mochi Host Command Guard (host_exec.py)
Ensures commands targeting 'mypc' are only executed when an OTP session is unlocked.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Import check_status from verify_otp in the same directory
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from verify_otp import check_status
except ImportError:
    def check_status():
        session_file = Path("/tmp/host_otp_session.json")
        if not session_file.exists():
            return {"unlocked": False}
        return {"unlocked": True}

def main():
    if len(sys.argv) < 2:
        print("Usage: host_exec.py <command_to_run_on_mypc>")
        sys.exit(1)

    cmd = " ".join(sys.argv[1:])

    status = check_status()
    if not status.get("unlocked", False):
        print("=================================================================")
        print("🔒 [SECURITY GUARD] Host PC execution is LOCKED.")
        print("Mochi must ask Conde for the 6-digit OTP before running commands on 'mypc'.")
        print("Conde can get the OTP from Google Authenticator or by running:")
        print("  .\\hermes\\get-otp.ps1 on Windows PC.")
        print("")
        print("Once received, unlock the session by running:")
        print("  python3 /data/hermes/scripts/verify_otp.py <6-digit-otp>")
        print("=================================================================")
        sys.exit(403)

    # Session is unlocked -> execute via SSH to 'mypc'
    ssh_cmd = ["ssh", "mypc", cmd]
    try:
        proc = subprocess.run(ssh_cmd, stdout=sys.stdout, stderr=sys.stderr)
        sys.exit(proc.returncode)
    except Exception as exc:
        print(f"Error executing remote SSH command: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
