# Dockerfile for College LAN Arcade Server
FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . /app

# Expose LAN Arcade default TCP port
EXPOSE 50555

# Run Arcade application
CMD ["python3", "lan_core.py"]
