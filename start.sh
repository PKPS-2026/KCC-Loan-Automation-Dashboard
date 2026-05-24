#!/bin/bash
# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &

# Start VNC server on the virtual display
x11vnc -display :99 -forever -nopw -quiet &

# Start noVNC websocket proxy (browser-accessible VNC on port 6080)
websockify --web /usr/share/novnc 6080 localhost:5900 &

# Wait for display to be ready
sleep 2

# Start Flask dashboard (Chrome will use DISPLAY=:99)
DISPLAY=:99 python /app/src/dashboard.py
