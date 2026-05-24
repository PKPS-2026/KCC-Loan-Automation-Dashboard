FROM python:3.11-slim-bookworm

# Install Chrome + virtual display + noVNC
RUN apt-get update && apt-get install -y \
    wget gnupg2 curl \
    xvfb x11vnc novnc websockify \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Entrypoint script
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 5000 6080

CMD ["./start.sh"]
