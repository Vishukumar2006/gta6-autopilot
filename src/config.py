"""Configuration manager for GTA 6 Autonomous Clipping & Publishing Pipeline."""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
CLIPS_DIR = OUTPUT_DIR / "clips"
TEMP_DIR = OUTPUT_DIR / "temp"
THUMBNAILS_DIR = OUTPUT_DIR / "thumbnails"
STATIC_DIR = BASE_DIR / "web" / "static"
CONFIG_FILE = BASE_DIR / "config.json"


@dataclass
class VideoConfig:
    width: int = 1080
    height: int = 1920
    low_spec_width: int = 720
    low_spec_height: int = 1280
    fps: int = 30
    min_clip_duration_sec: int = 18
    max_clip_duration_sec: int = 58
    max_cpu_threads: int = 2
    ffmpeg_preset: str = "ultrafast"  # ultrafast, superfast, veryfast
    hw_accel: str = "auto"  # auto, nvenc, qsv, amf, none
    banner_bg_color: str = "#FF007F"  # Vice City Neon Pink
    banner_text_color: str = "#FFFFFF"
    subtitles_color: str = "#FFE600"  # Bold Viral Yellow
    subtitles_font_size: int = 42


@dataclass
class StreamConfig:
    keywords: List[str] = field(
        default_factory=lambda: [
            "GTA 6",
            "Grand Theft Auto VI",
            "GTA VI gameplay",
            "GTA 6 leaks",
            "Rockstar Games GTA 6",
            "Vice City GTA 6",
        ]
    )
    min_view_count: int = 25
    poll_interval_seconds: int = 180
    max_streams_per_cycle: int = 3
    chunk_record_duration_sec: int = 120  # download in 2-minute chunks to save RAM


@dataclass
class SocialConfig:
    dry_run: bool = True  # True: simulate uploads with realistic logs; False: live API
    youtube_client_secrets_file: str = ""
    youtube_token_file: str = ""
    youtube_channel_id: str = ""
    youtube_default_tags: List[str] = field(
        default_factory=lambda: [
            "gta6",
            "gtavi",
            "gta 6",
            "rockstargames",
            "gaming",
            "shorts",
            "vicecity",
            "viral",
        ]
    )
    instagram_access_token: str = ""
    instagram_account_id: str = ""
    min_interval_between_posts_minutes: int = 60
    max_posts_per_day: int = 18


@dataclass
class SystemConfig:
    low_spec_mode: bool = True  # Optimized for budget PC specs
    port: int = 8080
    host: str = "0.0.0.0"  # Allows access from mobile devices on local Wi-Fi
    log_level: str = "INFO"
    video: VideoConfig = field(default_factory=VideoConfig)
    stream: StreamConfig = field(default_factory=StreamConfig)
    social: SocialConfig = field(default_factory=SocialConfig)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        video_data = data.get("video", {})
        stream_data = data.get("stream", {})
        social_data = data.get("social", {})

        return cls(
            low_spec_mode=data.get("low_spec_mode", True),
            port=data.get("port", 8080),
            host=data.get("host", "0.0.0.0"),
            log_level=data.get("log_level", "INFO"),
            video=VideoConfig(**video_data) if isinstance(video_data, dict) else VideoConfig(),
            stream=StreamConfig(**stream_data) if isinstance(stream_data, dict) else StreamConfig(),
            social=SocialConfig(**social_data) if isinstance(social_data, dict) else SocialConfig(),
        )

    def save(self, filepath: Path = CONFIG_FILE) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Path = CONFIG_FILE) -> "SystemConfig":
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls.from_dict(data)
            except Exception:
                pass
        cfg = cls()
        cfg.save(filepath)
        return cfg


def ensure_directories():
    """Ensure all required runtime directories exist."""
    for d in [DATA_DIR, OUTPUT_DIR, CLIPS_DIR, TEMP_DIR, THUMBNAILS_DIR, STATIC_DIR]:
        d.mkdir(parents=True, exist_ok=True)
