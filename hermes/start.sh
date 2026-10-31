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
mkdir -p /data/hermes /data/tailscale /data/ssh

# Symlink ~/.hermes -> /data/hermes so config, memories, and skills persist across redeploys
if [ -d "$HOME/.hermes" ] && [ ! -L "$HOME/.hermes" ]; then
    echo "Migrating template files from $HOME/.hermes to /data/hermes..."
    cp -rn "$HOME/.hermes/." /data/hermes/ 2>/dev/null || true
    rm -rf "$HOME/.hermes"
fi
ln -sfn /data/hermes "$HOME/.hermes"

# 4. Start Tailscale in userspace networking mode
echo "Starting tailscaled (userspace networking mode)..."
tailscaled --tun=userspace-networking --state=/data/tailscale/tailscaled.state --socket=/tmp/tailscaled.sock &

# Ensure standard socket location links to /tmp/tailscaled.sock for convenience
mkdir -p /var/run/tailscale
ln -sf /tmp/tailscaled.sock /var/run/tailscale/tailscaled.sock 2>/dev/null || true

# Wait until tailscaled is ready (polling tailscale status, no blind sleep)
echo "Waiting for tailscaled socket to become responsive..."
until tailscale --socket=/tmp/tailscaled.sock status >/dev/null 2>&1; do
    sleep 0.5
done
echo "tailscaled socket is ready."

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

# 6. Finally exec the Hermes gateway (for Discord/Telegram messaging)
echo "Executing Hermes gateway..."
exec hermes gateway
