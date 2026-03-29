FROM python:3.12-slim

# Install ttyd (binary from GitHub releases) + Caddy + shell tools
ARG TTYD_VERSION=1.7.7
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash tmux git curl ca-certificates debian-keyring debian-archive-keyring apt-transport-https \
    && curl -fsSL -o /usr/local/bin/ttyd \
       "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.x86_64" \
    && chmod +x /usr/local/bin/ttyd \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update && apt-get install -y --no-install-recommends caddy \
    && apt-get purge -y curl && apt-get autoremove -y \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY clidestable/ clidestable/
COPY templates/ templates/
COPY Caddyfile .
COPY entrypoint.sh .
RUN pip install --no-cache-dir . && chmod +x entrypoint.sh

# Single external port — Caddy routes everything
EXPOSE 7690

# Log dir + stall working dir
VOLUME ["/data"]

CMD ["./entrypoint.sh"]
