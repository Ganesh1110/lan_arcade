# Dockerfile for Single-Server College LAN Arcade Deployment
FROM python:3.11-slim

# Install ttyd for zero-install web browser terminal access
RUN apt-get update && apt-get install -y ttyd curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app

# Expose Web Browser port (8080) and Arcade TCP port (50555)
EXPOSE 8080 50555

# Default Command
CMD ["python3", "lan_core.py", "--server"]
