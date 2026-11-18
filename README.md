# 🌴 GTA 6 Autopilot: 24/7 Autonomous Clipping & Cross-Posting System

An autonomous, 100% hands-free pipeline built for GTA 6 clipping channels on **YouTube Shorts** and **Instagram Reels**.

Configured to run **24/7 continuously in the Cloud without needing your PC to stay on**, posting **10–20 viral clips daily**, and accessible from your mobile phone anywhere in the world.

---

## ☁️ 24/7 Cloud Deployment (PC NOT REQUIRED)

To run 24/7 while your PC is completely powered off, deploy using any of the three cloud methods below:

### Option 1: 1-Click Cloud Deployment (Railway / Render) — *Recommended for Mobile*
1. Push this folder to a GitHub repository or upload to **Railway** (or **Render**).
2. Railway will automatically detect the [Dockerfile](file:///C:/Users/Bablu%20Kumar%20PC/.gemini/antigravity/scratch/gta6-autopilot/Dockerfile) and [railway.json](file:///C:/Users/Bablu%20Kumar%20PC/.gemini/antigravity/scratch/gta6-autopilot/railway.json).
3. Railway provides a free, secure public HTTPS URL (e.g. `https://gta6-autopilot.up.railway.app`).
4. **Result:** Open that URL on your phone anywhere (4G/5G/Wi-Fi). It runs 24/7 with zero PC required.

### Option 2: Free Linux VPS (Oracle Cloud Always Free / DigitalOcean / AWS EC2)
1. Launch any Ubuntu/Debian Linux VPS.
2. Upload this directory and execute the automated setup script:
   ```bash
   chmod +x setup_vps.sh
   ./setup_vps.sh
   ```
3. The script installs FFmpeg, Python, yt-dlp, and registers a persistent `systemd` service (`gta6-autopilot.service`) that starts on boot and restarts automatically if it ever crashes.
4. **Result:** Access your mobile dashboard at `http://<YOUR_VPS_PUBLIC_IP>:8080`. Your PC can remain off.

### Option 3: Docker Container
```bash
docker compose up -d --build
```

---

## 📈 10–20 Clips Daily Posting Schedule

The engine is tuned in [config.json](file:///C:/Users/Bablu%20Kumar%20PC/.gemini/antigravity/scratch/gta6-autopilot/config.json) to publish up to **18 clips per day** spaced across 24 hours:
- `max_posts_per_day: 18` (10–20 clips per day)
- `min_interval_between_posts_minutes: 60` (1 clip posted every ~60–80 minutes)
- This rhythm matches YouTube Shorts & Instagram Reels algorithm sweet spots without triggering spam filters.

---

## 🚀 Key Features

1. **Autonomous Live Stream Finder**:
   - Continuously monitors YouTube for active GTA 6 live streams, high-engagement gameplay, and leak broadcasts.
   - Intelligent deduplication: never downloads or processes the same stream twice.

2. **Smart Viral Highlight Detection**:
   - Audio energy / RMS peak detection catches explosions, police chases, streamer reactions, and epic fails.
   - Cuts clips between 18s and 58s (optimal for YouTube Shorts & Instagram Reels algorithms).
   - Generates high-converting Hook titles, descriptions, and targeted viral hashtags.

3. **9:16 Vertical Video Formatter**:
   - Converts standard 16:9 horizontal gameplay to 9:16 vertical without distortion.
   - Blurred background with centered sharp action.
   - High-contrast top hook banner (`WAIT UNTIL THE END... 😱`).
   - Automatic thumbnail generation for maximum CTR.

4. **100% Autonomous Cross-Poster**:
   - Direct integration with **YouTube Data API v3** (Shorts category: Gaming).
   - Direct integration with **Meta / Instagram Graph API** (Reels).
   - Smart rate limiter & queue manager prevents account bans or spam flags.
   - Safe **Dry-Run Mode** enabled by default for zero-risk testing before adding live credentials.

5. **Universal Mobile Dashboard**:
   - Access from your smartphone browser (iPhone / Android) over any network (4G/5G/Wi-Fi).
   - Live video previews, queue monitor, stream table, system logs, and one-click manual triggers.

---

## ⚙️ Configuration & Live Publishing

System settings are stored in `config.json`. To connect live social accounts:

### YouTube Shorts
1. Download OAuth2 client secrets from Google Cloud Console (`client_secrets.json`).
2. Set `"youtube_token_file": "path/to/token.json"` in `config.json`.
3. Set `"dry_run": false` in `config.json`.

### Instagram Reels
1. Obtain an Instagram Graph API User Access Token from Meta Developer Portal.
2. Set `"instagram_access_token": "YOUR_TOKEN"` and `"instagram_account_id": "YOUR_IG_ID"`.
3. Set `"dry_run": false` in `config.json`.
