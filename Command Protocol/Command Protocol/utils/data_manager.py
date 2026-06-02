"""
Data Manager — handles all JSON read/write operations for persistent storage.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

log = logging.getLogger("CommandProtocol.DataManager")

DATA_DIR = Path(__file__).parent.parent / "data"


class DataManager:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self._ensure_defaults()

    def _ensure_defaults(self):
        """Create default data files if they don't exist."""
        defaults = {
            "game_info.json": self._default_game_info(),
            "suggestions.json": {"suggestions": []},
            "bug_reports.json": {"reports": []},
            "devlog.json": self._default_devlog(),
            "changelog.json": self._default_changelog(),
            "progress.json": self._default_progress(),
            "roadmap.json": self._default_roadmap(),
        }

        for filename, default_data in defaults.items():
            path = DATA_DIR / filename
            if not path.exists():
                self._write(filename, default_data)
                log.info(f"Created default data file: {filename}")

    # ── Core I/O ──────────────────────────────────────────────────────────────

    def _read(self, filename: str) -> dict:
        path = DATA_DIR / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            log.error(f"Error reading {filename}: {e}")
            return {}

    def _write(self, filename: str, data: dict) -> bool:
        path = DATA_DIR / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            log.error(f"Error writing {filename}: {e}")
            return False

    # ── Suggestions ───────────────────────────────────────────────────────────

    def add_suggestion(self, user_id: int, username: str, suggestion: str) -> int:
        data = self._read("suggestions.json")
        suggestions = data.get("suggestions", [])
        new_id = len(suggestions) + 1
        suggestions.append({
            "id": new_id,
            "user_id": user_id,
            "username": username,
            "suggestion": suggestion,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
        })
        data["suggestions"] = suggestions
        self._write("suggestions.json", data)
        return new_id

    def get_suggestions(self) -> list:
        return self._read("suggestions.json").get("suggestions", [])

    # ── Bug Reports ───────────────────────────────────────────────────────────

    def add_bug_report(self, user_id: int, username: str, title: str,
                       description: str, steps: str, severity: str) -> int:
        data = self._read("bug_reports.json")
        reports = data.get("reports", [])
        new_id = len(reports) + 1
        reports.append({
            "id": new_id,
            "user_id": user_id,
            "username": username,
            "title": title,
            "description": description,
            "steps": steps,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "open",
        })
        data["reports"] = reports
        self._write("bug_reports.json", data)
        return new_id

    def get_bug_reports(self) -> list:
        return self._read("bug_reports.json").get("reports", [])

    # ── Game Info / Dev Data ──────────────────────────────────────────────────

    def get_game_info(self) -> dict:
        return self._read("game_info.json")

    def get_devlog(self) -> dict:
        return self._read("devlog.json")

    def update_devlog(self, title: str, content: str, author: str) -> bool:
        data = {
            "title": title,
            "content": content,
            "author": author,
            "date": datetime.utcnow().strftime("%B %d, %Y"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        return self._write("devlog.json", data)

    def get_changelog(self) -> dict:
        return self._read("changelog.json")

    def update_changelog(self, version: str, notes: str, author: str) -> bool:
        data = {
            "version": version,
            "notes": notes,
            "author": author,
            "date": datetime.utcnow().strftime("%B %d, %Y"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        return self._write("changelog.json", data)

    def get_progress(self) -> dict:
        return self._read("progress.json")

    def update_progress(self, data: dict) -> bool:
        return self._write("progress.json", data)

    def get_roadmap(self) -> dict:
        return self._read("roadmap.json")

    # ── Default Data ──────────────────────────────────────────────────────────

    def _default_game_info(self) -> dict:
        return {
            "name": "Command Protocol",
            "tagline": "Wage war. Build empires. Control the field.",
            "description": (
                "Command Protocol is a tactical real-time strategy game set in a near-future "
                "world fractured by corporate warfare and armed rebellion. Players command elite "
                "military forces or join the decentralized Rebel Movement to seize control of "
                "strategic nodes across a devastated globe.\n\n"
                "Build bases, deploy specialized units, research advanced weaponry, and outmaneuver "
                "your enemies through superior strategy. Every decision carries weight. Every resource "
                "matters. Victory belongs to the most disciplined commander."
            ),
            "genre": "Real-Time Strategy",
            "platform": "PC (Windows / Linux)",
            "status": "In Development — Alpha Phase",
            "version": "0.4.2-alpha",
            "developer": "Command Protocol Dev Team",
        }

    def _default_devlog(self) -> dict:
        return {
            "title": "Alpha Systems — First Contact",
            "content": (
                "• Core movement and pathfinding engine is operational.\n"
                "• Unit selection and command system implemented.\n"
                "• Basic resource extraction nodes placed on Test Map 01.\n"
                "• Army faction HQ building prototype is in-engine.\n"
                "• Rebel faction guerrilla spawn logic drafted.\n"
                "• Next up: combat resolution system and fog of war."
            ),
            "author": "Lead Developer",
            "date": "June 1, 2025",
            "timestamp": "2025-06-01T00:00:00",
        }

    def _default_changelog(self) -> dict:
        return {
            "version": "v0.4.2-alpha",
            "notes": (
                "**New:**\n"
                "• Added unit experience and veterancy system\n"
                "• Implemented basic terrain elevation logic\n"
                "• New Army unit: Heavy Assault Mech (placeholder model)\n\n"
                "**Fixed:**\n"
                "• Units no longer clip through base walls\n"
                "• Resource counter no longer goes negative\n"
                "• Fixed crash on map load with >16 units\n\n"
                "**Known Issues:**\n"
                "• Pathfinding stutters on maps larger than 512x512\n"
                "• Rebel faction units occasionally ignore attack orders"
            ),
            "author": "Dev Team",
            "date": "June 1, 2025",
            "timestamp": "2025-06-01T00:00:00",
        }

    def _default_progress(self) -> dict:
        return {
            "version": "v0.4.2-alpha",
            "current_objective": "Complete core combat loop and begin faction balance testing",
            "overall_percent": 28,
            "completed": [
                "Project scaffolding & engine setup",
                "Core movement & pathfinding engine",
                "Unit selection and command framework",
                "Resource extraction system",
                "Basic UI / HUD prototype",
                "Army faction HQ building",
                "Map editor (internal)",
                "Lobby / session system",
            ],
            "in_progress": [
                "Combat resolution system (60%)",
                "Fog of war (40%)",
                "Rebel faction unique mechanics (30%)",
                "Unit veterancy / experience system (75%)",
                "Terrain elevation & cover bonuses (20%)",
            ],
            "upcoming": [
                "Multiplayer networking layer",
                "Campaign mode — Chapter 1",
                "Full faction tech trees",
                "Sound design & music",
                "Official map pack (10 maps)",
            ],
        }

    def _default_roadmap(self) -> dict:
        return {
            "phases": [
                {
                    "name": "Phase 1 — Foundation",
                    "status": "complete",
                    "items": [
                        "Engine setup & core architecture",
                        "Movement, selection, and command systems",
                        "Resource extraction & economy",
                        "Basic HUD and UI framework",
                    ],
                },
                {
                    "name": "Phase 2 — Combat & Factions",
                    "status": "active",
                    "items": [
                        "Combat resolution engine",
                        "Fog of war & vision system",
                        "Army faction full unit roster",
                        "Rebel faction unique mechanics",
                        "Terrain & cover system",
                    ],
                },
                {
                    "name": "Phase 3 — Multiplayer & Polish",
                    "status": "upcoming",
                    "items": [
                        "Multiplayer networking layer",
                        "Ranked matchmaking system",
                        "Balance pass — all factions",
                        "Sound design & score",
                    ],
                },
                {
                    "name": "Phase 4 — Campaign & Release",
                    "status": "upcoming",
                    "items": [
                        "Campaign mode — 12 missions",
                        "Full tutorial sequence",
                        "Performance optimization",
                        "Early Access launch",
                    ],
                },
            ]
        }
