#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "          Hermes Agent Container Starting Up              "
echo "=========================================================="

# 1. Validate required environment variables
missing_vars=()
[ -z "${TS_AUTHKEY:-}" ] && missing_vars+=("TS_AUTHKEY")
[ -z "${SSH_PRIVATE_KEY:-}" ] && missing_vars+=("SSH_PRIVATE_KEY")
[ -z "${PC_TAILSCALE_HOST:-}" ] && missing_vars+=("PC_TAILSCALE_HOST")
[ -z "${PC_USER:-}" ] && missing_vars+=("PC_USER")

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "ERROR: Missing required environment variable(s):" >&2
    for var in "${missing_vars[@]}"; do
        echo "  - $var" >&2
    done
    echo "" >&2
    echo "Please configure these variables in your Railway service settings." >&2
    echo "Refer to hermes/.env.example and hermes/README.md for details." >&2
    exit 1
fi

# Optional warnings for bot tokens and LLM provider keys
if [ -z "${DISCORD_BOT_TOKEN:-}" ] && [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "WARNING: Neither DISCORD_BOT_TOKEN nor TELEGRAM_BOT_TOKEN is set." >&2
    echo "Hermes messaging gateway requires a bot token to accept messages." >&2
fi

if [ -z "${OPENROUTER_API_KEY:-}" ] && [ -z "${NOUS_API_KEY:-}" ] && [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${GOOGLE_API_KEY:-}" ]; then
    echo "WARNING: No primary LLM API key detected (OPENROUTER_API_KEY, NOUS_API_KEY, etc.)." >&2
fi

# 2. Defaults for optional variables
TS_HOSTNAME="${TS_HOSTNAME:-hermes-railway}"
PC_SSH_PORT="${PC_SSH_PORT:-22}"

# 3. Persistent directories on Railway Volume (/data)
echo "Ensuring persistent directories exist on /data..."
mkdir -p /data/hermes /data/tailscale /data/ssh /data/hermes/scripts /data/hermes/cron /data/hermes/skins /data/hermes/memories

# Sync bundled Hermes configuration (SOUL.md, config.yaml, memories, skins, cron, scripts) to /data/hermes
if [ -d "/app/config" ]; then
    echo "Syncing bundled Hermes configuration to /data/hermes..."
    cp -rf /app/config/* /data/hermes/
fi

# Ensure scripts are executable
chmod +x /data/hermes/scripts/*.py 2>/dev/null || true

# Write environment variables into /data/hermes/.env for scripts and tools
cat <<EOF > /data/hermes/.env
DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN:-}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
EOF
chmod 600 /data/hermes/.env

# Optional auth.json if passed via AUTH_JSON environment variable
if [ -n "${AUTH_JSON:-}" ]; then
    echo "Writing AUTH_JSON into /data/hermes/auth.json..."
    printf '%s\n' "$AUTH_JSON" > /data/hermes/auth.json
    chmod 600 /data/hermes/auth.json
fi

# Symlink ~/.hermes -> /data/hermes so config, memories, and skills persist across redeploys
rm -rf "$HOME/.hermes"
ln -sfn /data/hermes "$HOME/.hermes"

# 4. Start Tailscale in userspace networking mode
echo "Starting tailscaled (userspace networking mode)..."
tailscaled --tun=userspace-networking --state=/data/tailscale/tailscaled.state --socket=/tmp/tailscaled.sock &

# Ensure standard socket location links to /tmp/tailscaled.sock for convenience
mkdir -p /var/run/tailscale
ln -sf /tmp/tailscaled.sock /var/run/tailscale/tailscaled.sock 2>/dev/null || true

# Wait until tailscaled is ready
echo "Waiting for tailscaled socket to become responsive..."
for i in $(seq 1 30); do
    if [ -S /tmp/tailscaled.sock ]; then
        out=$(tailscale --socket=/tmp/tailscaled.sock status 2>&1 || true)
        if ! echo "$out" | grep -q "connection refused"; then
            echo "tailscaled socket is ready."
            break
        fi
    fi
    sleep 0.5
done

# Authenticate with Tailscale network
echo "Connecting to Tailscale network as '${TS_HOSTNAME}'..."
tailscale --socket=/tmp/tailscaled.sock up --authkey="$TS_AUTHKEY" --hostname="$TS_HOSTNAME"
echo "Tailscale connected."

# 5. Configure SSH client and host aliases
echo "Configuring SSH key and ~/.ssh/config..."
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# Handle SSH private key whether pasted with actual newlines or literal '\n'
printf '%b\n' "$SSH_PRIVATE_KEY" > "$HOME/.ssh/id_ed25519"
chmod 600 "$HOME/.ssh/id_ed25519"

# Configure host alias 'mypc' and direct $PC_TAILSCALE_HOST address via Tailscale proxy
cat <<EOF > "$HOME/.ssh/config"
Host mypc $PC_TAILSCALE_HOST
    HostName $PC_TAILSCALE_HOST
    User $PC_USER
    Port $PC_SSH_PORT
    ProxyCommand tailscale --socket=/tmp/tailscaled.sock nc %h %p
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
    UserKnownHostsFile /data/ssh/known_hosts
    ServerAliveInterval 30
EOF
chmod 600 "$HOME/.ssh/config"

echo "SSH configuration complete. Host alias 'mypc' configured."

# Ensure hermes binary path is exported
export PATH="/root/.local/bin:/opt/hermes-agent/.hermes/bin:$PATH"

# 6. Test SSH connectivity to target Windows PC
echo "Testing Tailscale SSH connection to target PC (${PC_TAILSCALE_HOST})..."
ssh_ok=false
for attempt in $(seq 1 5); do
    if ssh -o BatchMode=yes -o ConnectTimeout=8 mypc "echo SSH_TUNNEL_SUCCESS" 2>&1 | grep -q "SSH_TUNNEL_SUCCESS"; then
        ssh_ok=true
        break
    fi
    echo "SSH attempt $attempt failed or still handshaking, retrying in 2 seconds..."
    sleep 2
done

if [ "$ssh_ok" = true ]; then
    echo "=========================================================="
    echo "SUCCESS: Hermes container successfully connected to PC!"
    echo "=========================================================="
else
    echo "WARNING: Could not connect to PC via SSH yet (might still be negotiating Tailscale route or PC is unreachable)."
fi

# 7. Finally start the Hermes messaging gateway or keep tunnel alive
if [ -n "${DISCORD_BOT_TOKEN:-}" ] || [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "Executing Hermes gateway..."
    exec hermes gateway
else
    echo "=========================================================="
    echo "Tailscale SSH tunnel is UP and RUNNING!"
    echo "To activate Discord/Telegram chat, configure DISCORD_BOT_TOKEN or TELEGRAM_BOT_TOKEN in Railway variables."
    echo "=========================================================="
    exec tail -f /dev/null
fi
