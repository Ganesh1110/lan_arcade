# Dockerfile for Centralized College LAN Arcade Server
FROM python:3.11-slim

# Install dependencies and download ttyd static binary
RUN apt-get update && apt-get install -y curl ca-certificates && \
    curl -fsSL https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app

# Expose Web Gateway (8080), Web Terminal port (8220), and Arcade TCP port (50555)
EXPOSE 8080 8220 50555

# Default Command
CMD ["python3", "lan_core.py", "--server"]
