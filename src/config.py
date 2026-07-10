import json
import os
from pathlib import Path

import yaml

from src.models import JobPost, ScoredJob

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"


def load_profile() -> dict:
    path = CONFIG_DIR / "profile.json"
    with open(path) as f:
        return json.load(f)


def load_settings() -> dict:
    path = CONFIG_DIR / "settings.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def get_env_or_raise(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f"Missing required env var: {key}")
    return val


def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def load_seen_jobs() -> set[str]:
    path = DATA_DIR / "seen.json"
    if not path.exists():
        return set()
    with open(path) as f:
        return set(json.load(f))


def save_seen_jobs(fingerprints: set[str]):
    path = DATA_DIR / "seen.json"
    with open(path, "w") as f:
        json.dump(sorted(fingerprints), f, indent=2)


def load_history() -> list[dict]:
    path = DATA_DIR / "history.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def append_history(entries: list[dict]):
    path = DATA_DIR / "history.json"
    history = load_history()
    history.extend(entries)
    with open(path, "w") as f:
        json.dump(history, f, indent=2, default=str)
