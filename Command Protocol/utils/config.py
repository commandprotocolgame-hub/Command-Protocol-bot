"""
Configuration manager — reads config.json and provides safe access.
"""

import json
import logging
from pathlib import Path

log = logging.getLogger("CommandProtocol.Config")

LOCAL_CONFIG_PATH = Path(__file__).parent.parent / "config.json"
RENDER_CONFIG_PATH = Path("/etc/secrets/config.json")

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
        if RENDER_CONFIG_PATH.exists():
            config_path = RENDER_CONFIG_PATH
            log.info("Using Render secret config.")
        elif LOCAL_CONFIG_PATH.exists():
            config_path = LOCAL_CONFIG_PATH
            log.info("Using local config.json.")
        else:
            log.warning("config.json not found — creating default config.")
            with open(LOCAL_CONFIG_PATH, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            self._data = DEFAULT_CONFIG.copy()
            return

        with open(config_path, "r") as f:
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