#!/usr/bin/env bash
set -e

echo "🌴 GTA 6 AUTOPILOT - 24/7 CLOUD SERVER SETUP 🌴"
echo "=================================================="

# 1. Install dependencies
echo "[*] Installing FFmpeg, Python 3, yt-dlp, and system fonts..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip ffmpeg fonts-dejavu-core curl

# Install latest yt-dlp
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp

# 2. Get current directory
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

mkdir -p data output/clips output/temp output/thumbnails

# 3. Create systemd 24/7 background service
echo "[*] Creating 24/7 systemd background service..."
SERVICE_FILE="/etc/systemd/system/gta6-autopilot.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=GTA 6 Autopilot 24/7 Autonomous Clipping & Cross-Posting Server
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/main.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable gta6-autopilot
sudo systemctl restart gta6-autopilot

PUBLIC_IP=$(curl -s https://api.ipify.org || echo "YOUR_VPS_IP")

echo "=================================================="
echo " [✓] 24/7 Autonomous Server is now ACTIVE and running!"
echo " [✓] Access from mobile phone anywhere in the world:"
echo "     http://$PUBLIC_IP:8080"
echo " [✓] Check logs with: sudo journalctl -u gta6-autopilot -f"
echo " [✓] Safe: Your PC can now be COMPLETELY TURNED OFF!"
echo "=================================================="
