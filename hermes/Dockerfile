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

# Install Hermes Agent using the official installer from NousResearch/hermes-agent repository
# Run in non-interactive headless mode without heavy desktop/browser packages
RUN curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | \
    bash -s -- --dir /opt/hermes-agent --non-interactive --skip-browser --skip-computer-use \
    && if [ -f /root/.local/bin/hermes ]; then ln -sf /root/.local/bin/hermes /usr/local/bin/hermes; fi

WORKDIR /app

# Copy configuration templates
COPY config/ /app/config/

# Copy container startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["bash", "/app/start.sh"]
