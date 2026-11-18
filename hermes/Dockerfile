FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:/opt/hermes-agent/.hermes/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    openssh-client \
    ca-certificates \
    iptables \
    && rm -rf /var/lib/apt/lists/*

# Install Tailscale via official install script
RUN curl -fsSL https://tailscale.com/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Install Hermes Agent pinned to the same upstream commit as Conde's local install,
# then apply the local patches (trigger_words, tool_permissions / channel tool
# filtering, Discord fixes). Upstream does not support those config keys, so an
# unpatched install silently ignores discord.tool_permissions.
# To upgrade: rebase the local patches, regenerate hermes/patches/, bump HERMES_COMMIT.
ARG HERMES_COMMIT=5ff11a689b561fdb1404aede3fafa543bbbb86bf
RUN curl -fsSL "https://raw.githubusercontent.com/NousResearch/hermes-agent/${HERMES_COMMIT}/scripts/install.sh" | \
    bash -s -- --dir /opt/hermes-agent --non-interactive --skip-browser --commit "${HERMES_COMMIT}" \
    && if [ -f /root/.local/bin/hermes ]; then ln -sf /root/.local/bin/hermes /usr/local/bin/hermes; fi

COPY patches/ /tmp/hermes-patches/
RUN test "$(git -C /opt/hermes-agent rev-parse HEAD)" = "${HERMES_COMMIT}" \
    && git -C /opt/hermes-agent -c user.name="Mochi Build" -c user.email=build@localhost am /tmp/hermes-patches/*.patch \
    && grep -q "tool_permissions" /opt/hermes-agent/gateway/config.py \
    && rm -rf /tmp/hermes-patches

WORKDIR /app

# Copy configuration templates
COPY config/ /app/config/

# Copy container startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["bash", "/app/start.sh"]
