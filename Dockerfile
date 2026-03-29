FROM python:3.12-slim

# Install ttyd + Caddy (both as static binaries) + shell tools
ARG TTYD_VERSION=1.7.7
ARG CADDY_VERSION=2.9.1
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash tmux git curl ca-certificates \
    && curl -fsSL -o /usr/local/bin/ttyd \
       "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.x86_64" \
    && chmod +x /usr/local/bin/ttyd \
    && curl -fsSL "https://github.com/caddyserver/caddy/releases/download/v${CADDY_VERSION}/caddy_${CADDY_VERSION}_linux_amd64.tar.gz" \
       | tar -xz -C /usr/local/bin caddy \
    && chmod +x /usr/local/bin/caddy \
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
