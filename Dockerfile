FROM python:3.12-slim

# Install ttyd + bash (for stall shells)
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    ttyd bash tmux git \
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
