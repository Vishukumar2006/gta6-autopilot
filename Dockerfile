FROM python:3.11-slim

# Install ffmpeg, yt-dlp, curl, fonts, and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    curl \
    ca-certificates \
    && curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY . /app

# Ensure directories exist
RUN mkdir -p /app/data /app/output/clips /app/output/temp /app/output/thumbnails

# Expose web dashboard port
EXPOSE 8080

# Run 24/7 autonomous pipeline
CMD ["python3", "main.py", "--host", "0.0.0.0", "--port", "8080"]
