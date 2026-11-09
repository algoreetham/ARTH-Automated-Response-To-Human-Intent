"""Configuration loader and manager for ARTH.
Loads settings from config.yaml and environment variables from .env.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


@dataclass
class BrainConfig:
    model: str = "gemma4:12b"
    fallback_model: str = "gemma4:e4b"
    ollama_host: str = "http://localhost:11434"
    context_window: int = 8192
    auto_start: bool = True
    startup_timeout: int = 10


@dataclass
class UserConfig:
    name: str = "Boss"


@dataclass
class VoiceConfig:
    wake_word: str = "ARTH"
    wake_word_sensitivity: str = "balanced"
    speed: str = "normal"
    languages: List[str] = field(default_factory=lambda: ["en", "hi", "kn"])
    tts_voice: str = "calm_female"


@dataclass
class QuietHoursConfig:
    enabled: bool = True
    start: str = "22:00"
    end: str = "07:00"


@dataclass
class FilesConfig:
    allowed_folder: str = "~/Desktop/ARTH_Workspace"

    @property
    def resolved_allowed_folder(self) -> Path:
        return Path(os.path.expanduser(self.allowed_folder)).resolve()


@dataclass
class SecurityConfig:
    voice_lock_enabled: bool = True
    max_password_attempts: int = 3
    lockout_duration_seconds: int = 300
    trusted_contact_email: str = ""


@dataclass
class SystemConfig:
    battery_alert_threshold: int = 15
    storage_alert_threshold: int = 10
    unprompted_suggestions: bool = True
    not_now_duration_seconds: int = 3600
    nudge_interval_seconds: int = 3600


@dataclass
class ArthConfig:
    brain: BrainConfig = field(default_factory=BrainConfig)
    user: UserConfig = field(default_factory=UserConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    quiet_hours: QuietHoursConfig = field(default_factory=QuietHoursConfig)
    files: FilesConfig = field(default_factory=FilesConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    system: SystemConfig = field(default_factory=SystemConfig)


def load_config(config_path: Path | str | None = None, env_path: Path | str | None = None) -> ArthConfig:
    """Load configuration from YAML and environment variables safely without crashing."""
    # 1. Load environment variables
    env_file = Path(env_path) if env_path else DEFAULT_ENV_PATH
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
    else:
        load_dotenv()

    # 2. Locate configuration file
    cfg_file = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    raw_cfg: Dict[str, Any] = {}

    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    raw_cfg = loaded
                else:
                    print(f"Warning: Configuration at '{cfg_file}' was empty or not a valid dictionary. Using default settings.")
        except Exception as e:
            print(f"Warning: Could not read configuration from '{cfg_file}': {e}. Using default settings.")
    else:
        print(f"Notice: Config file '{cfg_file}' not found. Using default settings.")

    # 3. Populate dataclasses with defaults overridden by yaml
    brain_data = raw_cfg.get("brain", {})
    user_data = raw_cfg.get("user", {})
    voice_data = raw_cfg.get("voice", {})
    quiet_data = raw_cfg.get("quiet_hours", {})
    files_data = raw_cfg.get("files", {})
    sec_data = raw_cfg.get("security", {})
    sys_data = raw_cfg.get("system", {})

    return ArthConfig(
        brain=BrainConfig(
            model=brain_data.get("model", "gemma4:12b"),
            fallback_model=brain_data.get("fallback_model", "gemma4:e4b"),
            ollama_host=os.getenv("OLLAMA_HOST", brain_data.get("ollama_host", "http://localhost:11434")),
            context_window=brain_data.get("context_window", 8192),
            auto_start=brain_data.get("auto_start", True),
            startup_timeout=brain_data.get("startup_timeout", 10),
        ),
        user=UserConfig(
            name=user_data.get("name", "Boss"),
        ),
        voice=VoiceConfig(
            wake_word=voice_data.get("wake_word", "ARTH"),
            wake_word_sensitivity=voice_data.get("wake_word_sensitivity", "balanced"),
            speed=voice_data.get("speed", "normal"),
            languages=voice_data.get("languages", ["en", "hi", "kn"]),
            tts_voice=voice_data.get("tts_voice", "calm_female"),
        ),
        quiet_hours=QuietHoursConfig(
            enabled=quiet_data.get("enabled", True),
            start=quiet_data.get("start", "22:00"),
            end=quiet_data.get("end", "07:00"),
        ),
        files=FilesConfig(
            allowed_folder=files_data.get("allowed_folder", "~/Desktop/ARTH_Workspace"),
        ),
        security=SecurityConfig(
            voice_lock_enabled=sec_data.get("voice_lock_enabled", True),
            max_password_attempts=sec_data.get("max_password_attempts", 3),
            lockout_duration_seconds=sec_data.get("lockout_duration_seconds", 300),
            trusted_contact_email=sec_data.get("trusted_contact_email", ""),
        ),
        system=SystemConfig(
            battery_alert_threshold=sys_data.get("battery_alert_threshold", 15),
            storage_alert_threshold=sys_data.get("storage_alert_threshold", 10),
            unprompted_suggestions=sys_data.get("unprompted_suggestions", True),
            not_now_duration_seconds=sys_data.get("not_now_duration_seconds", 3600),
            nudge_interval_seconds=sys_data.get("nudge_interval_seconds", 3600),
        ),
    )
