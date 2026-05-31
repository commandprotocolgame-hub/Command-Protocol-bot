"""
Embed factory — all embeds in Command Protocol style.
Consistent branding, colors, and formatting across every response.
"""

import discord
from datetime import datetime


# ─── Brand Colors ───────────────────────────────────────────────────────────────
class Colors:
    PRIMARY   = 0x00B4FF   # Electric blue — default
    ARMY      = 0x2E86AB   # Steel blue — Army faction
    REBELS    = 0xE63946   # Crimson red — Rebel faction
    SUCCESS   = 0x00FF87   # Matrix green — confirmations
    WARNING   = 0xFFBE0B   # Amber — caution
    ERROR     = 0xFF3860   # Red alert
    NEUTRAL   = 0x8B9BB4   # Slate — info / lore
    ADMIN     = 0xAA00FF   # Purple — admin actions
    DARK      = 0x0D1117   # Near black


# ─── Footer ─────────────────────────────────────────────────────────────────────
FOOTER_TEXT = "COMMAND PROTOCOL  //  COMMAND TERMINAL v1.0"
FOOTER_ICON = None  # Set to a URL if you have a bot avatar URL

# ─── Faction Icons ──────────────────────────────────────────────────────────────
ARMY_ICON   = "🎖️"
REBELS_ICON = "✊"
BOT_ICON    = "🖥️"
LOCK_ICON   = "🔒"
SIGNAL_ICON = "📡"
ALERT_ICON  = "⚠️"
CHECK_ICON  = "✅"
CROSS_ICON  = "❌"
STAR_ICON   = "★"


def base_embed(
    title: str,
    description: str = None,
    color: int = Colors.PRIMARY,
    url: str = None,
) -> discord.Embed:
    """Creates a base-styled embed with CP branding."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        url=url,
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def success_embed(title: str, description: str) -> discord.Embed:
    return base_embed(f"{CHECK_ICON}  {title}", description, Colors.SUCCESS)


def error_embed(title: str, description: str) -> discord.Embed:
    return base_embed(f"{CROSS_ICON}  {title}", description, Colors.ERROR)


def warning_embed(title: str, description: str) -> discord.Embed:
    return base_embed(f"{ALERT_ICON}  {title}", description, Colors.WARNING)


def info_embed(title: str, description: str) -> discord.Embed:
    return base_embed(f"{SIGNAL_ICON}  {title}", description, Colors.PRIMARY)


def admin_embed(title: str, description: str) -> discord.Embed:
    return base_embed(f"{LOCK_ICON}  {title}", description, Colors.ADMIN)


def army_embed(title: str, description: str) -> discord.Embed:
    return base_embed(f"{ARMY_ICON}  {title}", description, Colors.ARMY)


def rebels_embed(title: str, description: str) -> discord.Embed:
    return base_embed(f"{REBELS_ICON}  {title}", description, Colors.REBELS)
