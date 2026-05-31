"""
Configuration manager — reads config.json and provides safe access.
"""

import json
import logging
from pathlib import Path

log = logging.getLogger("CommandProtocol.Config")

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

DEFAULT_CONFIG = {
    "BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
    "GUILD_ID": "",
    "ADMIN_ROLE_IDS": [],
    "ARMY_ROLE_ID": "",
    "REBELS_ROLE_ID": "",
    "SUGGESTION_CHANNEL_ID": "",
    "BUGREPORT_CHANNEL_ID": "",
    "ANNOUNCE_CHANNEL_ID": "",
    "DEVLOG_CHANNEL_ID": "",
}


class Config:
    def __init__(self):
        self._data = {}
        self._load()

    def _load(self):
        if not CONFIG_PATH.exists():
            log.warning("config.json not found — creating default config.")
            with open(CONFIG_PATH, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            self._data = DEFAULT_CONFIG.copy()
        else:
            with open(CONFIG_PATH, "r") as f:
                self._data = json.load(f)
            log.info("Config loaded successfully.")

    def get(self, key: str, fallback=None):
        return self._data.get(key, fallback)

    def get_int(self, key: str, fallback: int = 0) -> int:
        val = self._data.get(key, fallback)
        try:
            return int(val) if val else fallback
        except (ValueError, TypeError):
            return fallback

    def get_list(self, key: str) -> list:
        return self._data.get(key, [])
