"""
Welcome Cog — automatic welcome messages for new members.

Features:
  - Auto welcome embed when a member joins
  - Posts in a configurable welcome channel
  - Optional DM welcome to the new member
  - Fully customizable message via /setwelcome
  - Optional auto-assign role on join
  - Preview command to test without someone joining
  - Toggle to enable/disable the system
  - /welcomeconfig to view current settings

Admin commands:
  /setwelcome      — Set the welcome channel + message
  /setwelcomedm    — Set or disable the DM message
  /welcomerole     — Set a role to auto-assign on join
  /welcometoggle   — Enable or disable welcome messages
  /welcomepreview  — Preview the welcome embed
  /welcomeconfig   — View current welcome settings
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
import json
from pathlib import Path
from typing import Optional

from utils.embeds import base_embed, success_embed, error_embed, warning_embed, Colors

log = logging.getLogger("CommandProtocol.Welcome")

DATA_DIR  = Path(__file__).parent.parent / "data"
WELCOME_FILE = DATA_DIR / "welcome.json"

# ─── Default Config ──────────────────────────────────────────────────────────────

DEFAULT_WELCOME = {
    "enabled": True,
    "channel_id": None,
    "dm_enabled": False,
    "dm_message": (
        "Welcome to **Command Protocol**, {mention}!\n\n"
        "Head to the server and pick your faction with `/join army` or `/join rebels`.\n"
        "Use `/about` to learn about the game and `/roadmap` to see what's coming.\n\n"
        "Good luck on the battlefield, Commander."
    ),
    "title": "NEW OPERATIVE DETECTED",
    "message": (
        "```\nINCOMING TRANSMISSION\nNEW OPERATIVE JOINED THE SERVER\n```\n\n"
        "Welcome to **Command Protocol**, {mention}! 🖥️\n\n"
        "You are recruit number **#{member_count}** to enter this command terminal.\n\n"
        "**Get started:**\n"
        "⚔️  Pick your side — `/join army` or `/join rebels`\n"
        "📡  Learn about the game — `/about`\n"
        "🗺️  See what's coming — `/roadmap`\n"
        "💡  Share ideas — `/suggest`\n\n"
        "Welcome to the fight, Commander."
    ),
    "color": Colors.SUCCESS,
    "show_avatar": True,
    "show_member_count": True,
    "auto_role_id": None,
}

# ─── Placeholders available in messages ──────────────────────────────────────────
# {mention}       — @mentions the new member
# {username}      — their username (no @)
# {display_name}  — their display name / nickname
# {member_count}  — current server member count
# {server}        — server name


# ─── JSON Helpers ────────────────────────────────────────────────────────────────

def _load() -> dict:
    if not WELCOME_FILE.exists():
        _save(DEFAULT_WELCOME.copy())
        return DEFAULT_WELCOME.copy()
    try:
        with open(WELCOME_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Backfill any missing keys from defaults
        for k, v in DEFAULT_WELCOME.items():
            data.setdefault(k, v)
        return data
    except (json.JSONDecodeError, OSError):
        return DEFAULT_WELCOME.copy()


def _save(data: dict):
    DATA_DIR.mkdir(exist_ok=True)
    with open(WELCOME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ─── Embed Builder ───────────────────────────────────────────────────────────────

def _build_welcome_embed(member: discord.Member, cfg: dict) -> discord.Embed:
    """Build the welcome embed for a given member using stored config."""

    def _fmt(text: str) -> str:
        return text.format(
            mention=member.mention,
            username=str(member),
            display_name=member.display_name,
            member_count=member.guild.member_count,
            server=member.guild.name,
        )

    embed = base_embed(
        title=_fmt(cfg.get("title", DEFAULT_WELCOME["title"])),
        description=_fmt(cfg.get("message", DEFAULT_WELCOME["message"])),
        color=cfg.get("color", Colors.SUCCESS),
    )

    if cfg.get("show_avatar", True):
        embed.set_thumbnail(url=member.display_avatar.url)

    if cfg.get("show_member_count", True):
        embed.set_footer(
            text=f"Member #{member.guild.member_count}  •  COMMAND PROTOCOL"
        )

    return embed


def _build_dm_embed(member: discord.Member, cfg: dict) -> discord.Embed:
    """Build the DM welcome embed."""

    def _fmt(text: str) -> str:
        return text.format(
            mention=member.mention,
            username=str(member),
            display_name=member.display_name,
            member_count=member.guild.member_count,
            server=member.guild.name,
        )

    return base_embed(
        title=f"👋  Welcome to {member.guild.name}",
        description=_fmt(cfg.get("dm_message", DEFAULT_WELCOME["dm_message"])),
        color=Colors.PRIMARY,
    )


# ─── Welcome Cog ────────────────────────────────────────────────────────────────

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── Admin guard ───────────────────────────────────────────────────────────────

    async def _check_admin(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        admin_role_ids = [int(rid) for rid in self.bot.config.get_list("ADMIN_ROLE_IDS") if rid]
        user_role_ids = [role.id for role in interaction.user.roles]
        if any(rid in user_role_ids for rid in admin_role_ids):
            return True
        embed = error_embed(
            "ACCESS DENIED",
            "```\nERROR 403: INSUFFICIENT CLEARANCE\nAdmin authorization required.\n```",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    # ── on_member_join event ──────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = _load()

        if not cfg.get("enabled", True):
            return

        # ── Auto-assign role ──────────────────────────────────────────────────────
        auto_role_id = cfg.get("auto_role_id")
        if auto_role_id:
            role = member.guild.get_role(int(auto_role_id))
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                except discord.Forbidden:
                    log.warning(f"Missing permissions to assign auto-role to {member}")

        # ── Welcome channel message ───────────────────────────────────────────────
        channel_id = cfg.get("channel_id")
        if channel_id:
            channel = member.guild.get_channel(int(channel_id))
            if channel:
                try:
                    embed = _build_welcome_embed(member, cfg)
                    await channel.send(content=member.mention, embed=embed)
                except discord.Forbidden:
                    log.warning(f"Missing permissions to send in welcome channel {channel_id}")
                except Exception as e:
                    log.error(f"Failed to send welcome message: {e}")

        # ── DM welcome ────────────────────────────────────────────────────────────
        if cfg.get("dm_enabled", False):
            try:
                dm_embed = _build_dm_embed(member, cfg)
                await member.send(embed=dm_embed)
            except (discord.Forbidden, discord.HTTPException):
                pass  # DMs closed — silently skip

    # ── /setwelcome ───────────────────────────────────────────────────────────────

    @app_commands.command(name="setwelcome", description="[ADMIN] Set the welcome channel and customize the welcome message.")
    @app_commands.describe(channel="Channel to send welcome messages in")
    async def setwelcome(self, interaction: discord.Interaction,
                         channel: discord.TextChannel):
        if not await self._check_admin(interaction):
            return

        cfg = _load()
        modal = SetWelcomeModal(cfg=cfg, channel_id=channel.id)
        await interaction.response.send_modal(modal)

    # ── /setwelcomedm ─────────────────────────────────────────────────────────────

    @app_commands.command(name="setwelcomedm", description="[ADMIN] Configure the DM sent to new members, or disable it.")
    @app_commands.describe(enabled="Enable or disable DM welcomes")
    async def setwelcomedm(self, interaction: discord.Interaction,
                           enabled: bool):
        if not await self._check_admin(interaction):
            return

        cfg = _load()

        if not enabled:
            cfg["dm_enabled"] = False
            _save(cfg)
            embed = success_embed("DM WELCOME DISABLED", "New members will no longer receive a DM on join.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        modal = SetWelcomeDMModal(cfg=cfg)
        await interaction.response.send_modal(modal)

    # ── /welcomerole ──────────────────────────────────────────────────────────────

    @app_commands.command(name="welcomerole", description="[ADMIN] Set a role to automatically assign to new members.")
    @app_commands.describe(role="Role to assign (leave blank to disable)")
    async def welcomerole(self, interaction: discord.Interaction,
                          role: Optional[discord.Role] = None):
        if not await self._check_admin(interaction):
            return

        cfg = _load()

        if role is None:
            cfg["auto_role_id"] = None
            _save(cfg)
            embed = success_embed("AUTO-ROLE DISABLED", "No role will be assigned to new members.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if role >= interaction.guild.me.top_role:
            embed = error_embed("ROLE TOO HIGH", "I cannot assign a role above my own. Move my role higher.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        cfg["auto_role_id"] = role.id
        _save(cfg)

        embed = success_embed(
            "AUTO-ROLE SET",
            f"New members will automatically receive the {role.mention} role when they join.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /welcometoggle ────────────────────────────────────────────────────────────

    @app_commands.command(name="welcometoggle", description="[ADMIN] Enable or disable the welcome message system.")
    async def welcometoggle(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return

        cfg = _load()
        cfg["enabled"] = not cfg.get("enabled", True)
        _save(cfg)

        if cfg["enabled"]:
            embed = success_embed(
                "WELCOME SYSTEM ENABLED",
                "New members will now receive a welcome message when they join.",
            )
        else:
            embed = warning_embed(
                "WELCOME SYSTEM DISABLED",
                "Welcome messages are now disabled. Use `/welcometoggle` again to re-enable.",
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /welcomepreview ───────────────────────────────────────────────────────────

    @app_commands.command(name="welcomepreview", description="[ADMIN] Preview what the welcome message will look like.")
    @app_commands.describe(target="Member to preview as (defaults to you)")
    async def welcomepreview(self, interaction: discord.Interaction,
                             target: Optional[discord.Member] = None):
        if not await self._check_admin(interaction):
            return

        member = target or interaction.user
        cfg = _load()

        embed = _build_welcome_embed(member, cfg)

        ch_id = cfg.get("channel_id")
        ch_str = f"<#{ch_id}>" if ch_id else "`Not set`"
        status_str = "`ENABLED`"  if cfg.get("enabled")    else "`DISABLED`"
        dm_str     = "`ON`"       if cfg.get("dm_enabled") else "`OFF`"

        header = base_embed(
            "🔍  WELCOME PREVIEW",
            f"This is a preview using **{member.display_name}** as the test member.\n"
            f"Channel: {ch_str}\n"
            f"Status: {status_str}\n"
            f"DM: {dm_str}",
            color=Colors.NEUTRAL,
        )

        await interaction.response.send_message(embeds=[header, embed], ephemeral=True)

        # Also preview the DM if enabled
        if cfg.get("dm_enabled"):
            dm_embed = _build_dm_embed(member, cfg)
            dm_header = base_embed(
                "📨  DM PREVIEW",
                "This is what the member would receive in their DMs:",
                color=Colors.NEUTRAL,
            )
            await interaction.followup.send(embeds=[dm_header, dm_embed], ephemeral=True)

    # ── /welcomeconfig ────────────────────────────────────────────────────────────

    @app_commands.command(name="welcomeconfig", description="[ADMIN] View the current welcome system configuration.")
    async def welcomeconfig(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return

        cfg = _load()

        channel_id  = cfg.get("channel_id")
        auto_role   = cfg.get("auto_role_id")
        status      = "`ENABLED ✅`"  if cfg.get("enabled")    else "`DISABLED ❌`"
        dm_status   = "`ENABLED ✅`"  if cfg.get("dm_enabled") else "`DISABLED ❌`"
        channel_str = f"<#{channel_id}>" if channel_id else "`Not configured`"
        role_str    = f"<@&{auto_role}>" if auto_role   else "`None`"

        embed = base_embed(
            "⚙️  WELCOME SYSTEM CONFIG",
            "```\nCOMMAND PROTOCOL — WELCOME MODULE\n```",
            color=Colors.ADMIN,
        )
        embed.add_field(name="Status",          value=status,      inline=True)
        embed.add_field(name="DM Welcome",      value=dm_status,   inline=True)
        embed.add_field(name="Auto-Role",       value=role_str,    inline=True)
        embed.add_field(name="Welcome Channel", value=channel_str, inline=True)
        embed.add_field(name="Show Avatar",     value="`Yes`" if cfg.get("show_avatar", True)       else "`No`", inline=True)
        embed.add_field(name="Member Count",    value="`Yes`" if cfg.get("show_member_count", True) else "`No`", inline=True)
        embed.add_field(
            name="Welcome Title",
            value=f"```{cfg.get('title', DEFAULT_WELCOME['title'])[:80]}```",
            inline=False,
        )
        embed.add_field(
            name="Message Preview (first 200 chars)",
            value=f"```{cfg.get('message', '')[:200]}```",
            inline=False,
        )
        embed.add_field(
            name="Available Placeholders",
            value="`{mention}` `{username}` `{display_name}` `{member_count}` `{server}`",
            inline=False,
        )
        embed.set_footer(text="Use /setwelcome to edit  •  COMMAND PROTOCOL")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── Set Welcome Modal ────────────────────────────────────────────────────────────

class SetWelcomeModal(discord.ui.Modal, title="Configure Welcome Message"):
    welcome_title = discord.ui.TextInput(
        label="Embed Title",
        placeholder="e.g. NEW OPERATIVE DETECTED",
        max_length=100,
        required=True,
    )
    message = discord.ui.TextInput(
        label="Welcome Message",
        placeholder="Use {mention} {username} {display_name} {member_count} {server}",
        style=discord.TextStyle.long,
        max_length=2000,
        required=True,
    )
    show_avatar = discord.ui.TextInput(
        label="Show member avatar? (yes / no)",
        placeholder="yes",
        max_length=3,
        required=False,
    )
    show_count = discord.ui.TextInput(
        label="Show member count in footer? (yes / no)",
        placeholder="yes",
        max_length=3,
        required=False,
    )

    def __init__(self, cfg: dict, channel_id: int):
        super().__init__()
        self._cfg = cfg
        self._channel_id = channel_id
        # Pre-fill with existing values
        self.welcome_title.default = cfg.get("title", DEFAULT_WELCOME["title"])[:100]
        self.message.default       = cfg.get("message", DEFAULT_WELCOME["message"])[:2000]
        self.show_avatar.default   = "yes" if cfg.get("show_avatar", True) else "no"
        self.show_count.default    = "yes" if cfg.get("show_member_count", True) else "no"

    async def on_submit(self, interaction: discord.Interaction):
        def _yn(field, default=True) -> bool:
            val = str(field).strip().lower()
            if val in ("yes", "y", "true", "1", ""):
                return True
            if val in ("no", "n", "false", "0"):
                return False
            return default

        self._cfg.update({
            "channel_id":       self._channel_id,
            "title":            str(self.welcome_title).strip(),
            "message":          str(self.message).strip(),
            "show_avatar":      _yn(self.show_avatar),
            "show_member_count":_yn(self.show_count),
        })
        _save(self._cfg)

        embed = success_embed(
            "WELCOME MESSAGE CONFIGURED",
            f"```\nOPERATION: WELCOME SETUP\nCHANNEL: #{interaction.guild.get_channel(self._channel_id).name if interaction.guild.get_channel(self._channel_id) else self._channel_id}\nSTATUS: SUCCESS\n```\n\n"
            f"Use `/welcomepreview` to see how it looks.\n"
            f"Use `/welcometoggle` to enable/disable.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── Set DM Modal ────────────────────────────────────────────────────────────────

class SetWelcomeDMModal(discord.ui.Modal, title="Configure DM Welcome"):
    dm_message = discord.ui.TextInput(
        label="DM Message",
        placeholder="Use {mention} {username} {display_name} {server} {member_count}",
        style=discord.TextStyle.long,
        max_length=2000,
        required=True,
    )

    def __init__(self, cfg: dict):
        super().__init__()
        self._cfg = cfg
        self.dm_message.default = cfg.get("dm_message", DEFAULT_WELCOME["dm_message"])[:2000]

    async def on_submit(self, interaction: discord.Interaction):
        self._cfg["dm_enabled"] = True
        self._cfg["dm_message"] = str(self.dm_message).strip()
        _save(self._cfg)

        embed = success_embed(
            "DM WELCOME CONFIGURED",
            "New members will now receive a DM when they join.\n\n"
            "Use `/welcomepreview` to see how the DM looks.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))