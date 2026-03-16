FROM python:3.12-slim

# Install ttyd (binary from GitHub releases) + shell tools
ARG TTYD_VERSION=1.7.7
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash tmux git curl ca-certificates \
    && curl -fsSL -o /usr/local/bin/ttyd \
       "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.x86_64" \
    && chmod +x /usr/local/bin/ttyd \
    && apt-get purge -y curl && apt-get autoremove -y \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY clidestable/ clidestable/
COPY templates/ templates/
RUN pip install --no-cache-dir .

EXPOSE 7690 7701-7720

# Log dir + stall working dir
VOLUME ["/data"]

CMD ["clidestable", "serve", "--port", "7690", "--log-dir", "/data"]
