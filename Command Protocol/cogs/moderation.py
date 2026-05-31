"""
Moderation Cog — full server moderation suite.

Commands:
  /ban         — Permanently ban a member
  /unban       — Unban a user by ID
  /kick        — Kick a member from the server
  /mute        — Timeout (mute) a member for a duration
  /unmute      — Remove a timeout from a member
  /warn        — Issue a warning (stored in JSON)
  /warnings    — View a member's warning history
  /clearwarns  — Clear all warnings for a member
  /purge       — Bulk delete messages in a channel
  /lockdown    — Lock a channel so members can't send messages
  /unlock      — Unlock a previously locked channel
  /slowmode    — Set slowmode delay on a channel
  /nick        — Force-change a member's nickname
  /role        — Add or remove a role from a member
  /modlog      — View recent moderation actions
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

from utils.embeds import (
    base_embed, success_embed, error_embed, warning_embed,
    Colors, LOCK_ICON, ALERT_ICON,
)

log = logging.getLogger("CommandProtocol.Moderation")

DATA_DIR = Path(__file__).parent.parent / "data"
WARNS_FILE = DATA_DIR / "warnings.json"
MODLOG_FILE = DATA_DIR / "modlog.json"

# Duration string → timedelta mapping for /mute
DURATION_MAP = {
    "60s":   timedelta(seconds=60),
    "5m":    timedelta(minutes=5),
    "10m":   timedelta(minutes=10),
    "30m":   timedelta(minutes=30),
    "1h":    timedelta(hours=1),
    "2h":    timedelta(hours=2),
    "6h":    timedelta(hours=6),
    "12h":   timedelta(hours=12),
    "1d":    timedelta(days=1),
    "3d":    timedelta(days=3),
    "7d":    timedelta(days=7),
    "28d":   timedelta(days=28),
}

DURATION_CHOICES = [
    app_commands.Choice(name="60 seconds",  value="60s"),
    app_commands.Choice(name="5 minutes",   value="5m"),
    app_commands.Choice(name="10 minutes",  value="10m"),
    app_commands.Choice(name="30 minutes",  value="30m"),
    app_commands.Choice(name="1 hour",      value="1h"),
    app_commands.Choice(name="2 hours",     value="2h"),
    app_commands.Choice(name="6 hours",     value="6h"),
    app_commands.Choice(name="12 hours",    value="12h"),
    app_commands.Choice(name="1 day",       value="1d"),
    app_commands.Choice(name="3 days",      value="3d"),
    app_commands.Choice(name="7 days",      value="7d"),
    app_commands.Choice(name="28 days",     value="28d"),
]


# ─── JSON Helpers ────────────────────────────────────────────────────────────────

def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(path: Path, data: dict):
    DATA_DIR.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ─── Warning Helpers ─────────────────────────────────────────────────────────────

def _add_warning(guild_id: int, user_id: int, username: str,
                 moderator: str, reason: str) -> int:
    data = _load(WARNS_FILE)
    key = str(guild_id)
    uid = str(user_id)
    data.setdefault(key, {}).setdefault(uid, [])
    data[key][uid].append({
        "id": len(data[key][uid]) + 1,
        "moderator": moderator,
        "username": username,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    })
    _save(WARNS_FILE, data)
    return len(data[key][uid])


def _get_warnings(guild_id: int, user_id: int) -> list:
    data = _load(WARNS_FILE)
    return data.get(str(guild_id), {}).get(str(user_id), [])


def _clear_warnings(guild_id: int, user_id: int):
    data = _load(WARNS_FILE)
    key = str(guild_id)
    if key in data and str(user_id) in data[key]:
        data[key][str(user_id)] = []
        _save(WARNS_FILE, data)


# ─── Mod Log Helpers ─────────────────────────────────────────────────────────────

def _log_action(guild_id: int, action: str, moderator: str,
                target: str, reason: str, extra: str = ""):
    data = _load(MODLOG_FILE)
    key = str(guild_id)
    data.setdefault(key, [])
    data[key].append({
        "action": action,
        "moderator": moderator,
        "target": target,
        "reason": reason,
        "extra": extra,
        "timestamp": datetime.utcnow().isoformat(),
    })
    # Keep last 200 entries per guild
    data[key] = data[key][-200:]
    _save(MODLOG_FILE, data)


def _get_modlog(guild_id: int, limit: int = 15) -> list:
    data = _load(MODLOG_FILE)
    return data.get(str(guild_id), [])[-limit:]


# ─── Permission Guard ─────────────────────────────────────────────────────────────

async def _deny(interaction: discord.Interaction, msg: str = None):
    embed = error_embed(
        "ACCESS DENIED",
        msg or (
            "```\nERROR 403: INSUFFICIENT CLEARANCE\n"
            "You do not have permission to execute this command.\n```"
        ),
    )
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


def _mod_embed(action: str, target: discord.Member | discord.User,
               moderator: discord.Member, reason: str,
               color: int = Colors.ERROR, extra: str = None) -> discord.Embed:
    """Standard moderation action embed."""
    embed = base_embed(f"🔨  {action}", color=color)
    embed.add_field(name="Target",     value=f"{target.mention} (`{target}`)", inline=True)
    embed.add_field(name="Moderator",  value=f"{moderator.mention}",           inline=True)
    embed.add_field(name="Reason",     value=reason or "No reason provided.",  inline=False)
    if extra:
        embed.add_field(name="Details", value=extra, inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)
    return embed


async def _try_dm(target: discord.Member, embed: discord.Embed):
    """Attempt to DM the target. Silently fail if DMs are closed."""
    try:
        await target.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass


# ─── Moderation Cog ──────────────────────────────────────────────────────────────

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /ban ──────────────────────────────────────────────────────────────────────

    @app_commands.command(name="ban", description="Permanently ban a member from the server.")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for the ban",
        delete_days="Days of messages to delete (0–7)",
    )
    @app_commands.choices(delete_days=[
        app_commands.Choice(name="Don't delete", value=0),
        app_commands.Choice(name="1 day",        value=1),
        app_commands.Choice(name="7 days",       value=7),
    ])
    async def ban(self, interaction: discord.Interaction,
                  member: discord.Member,
                  reason: Optional[str] = "No reason provided.",
                  delete_days: int = 0):
        if not interaction.user.guild_permissions.ban_members:
            return await _deny(interaction)
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await _deny(interaction, "You cannot ban someone with an equal or higher role.")
        if member == interaction.guild.me:
            return await _deny(interaction, "I cannot ban myself.")

        dm_embed = base_embed(
            "⛔  You have been banned",
            f"**Server:** {interaction.guild.name}\n**Reason:** {reason}",
            color=Colors.ERROR,
        )
        await _try_dm(member, dm_embed)

        await member.ban(reason=f"{interaction.user} — {reason}", delete_message_days=delete_days)
        _log_action(interaction.guild_id, "BAN", str(interaction.user), str(member), reason)

        embed = _mod_embed("MEMBER BANNED", member, interaction.user, reason, Colors.ERROR)
        await interaction.response.send_message(embed=embed)

    # ── /unban ────────────────────────────────────────────────────────────────────

    @app_commands.command(name="unban", description="Unban a user by their Discord ID.")
    @app_commands.describe(user_id="The Discord user ID to unban", reason="Reason for unban")
    async def unban(self, interaction: discord.Interaction,
                    user_id: str,
                    reason: Optional[str] = "No reason provided."):
        if not interaction.user.guild_permissions.ban_members:
            return await _deny(interaction)
        await interaction.response.defer()

        try:
            uid = int(user_id.strip())
        except ValueError:
            embed = error_embed("INVALID ID", "Please provide a valid numeric Discord user ID.")
            return await interaction.followup.send(embed=embed, ephemeral=True)

        try:
            ban_entry = await interaction.guild.fetch_ban(discord.Object(id=uid))
            user = ban_entry.user
        except discord.NotFound:
            embed = error_embed("NOT FOUND", f"No ban found for user ID `{uid}`.")
            return await interaction.followup.send(embed=embed, ephemeral=True)

        await interaction.guild.unban(user, reason=f"{interaction.user} — {reason}")
        _log_action(interaction.guild_id, "UNBAN", str(interaction.user), str(user), reason)

        embed = _mod_embed("MEMBER UNBANNED", user, interaction.user, reason, Colors.SUCCESS)
        await interaction.followup.send(embed=embed)

    # ── /kick ─────────────────────────────────────────────────────────────────────

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    async def kick(self, interaction: discord.Interaction,
                   member: discord.Member,
                   reason: Optional[str] = "No reason provided."):
        if not interaction.user.guild_permissions.kick_members:
            return await _deny(interaction)
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await _deny(interaction, "You cannot kick someone with an equal or higher role.")
        if member == interaction.guild.me:
            return await _deny(interaction, "I cannot kick myself.")

        dm_embed = base_embed(
            "🥾  You have been kicked",
            f"**Server:** {interaction.guild.name}\n**Reason:** {reason}",
            color=Colors.WARNING,
        )
        await _try_dm(member, dm_embed)

        await member.kick(reason=f"{interaction.user} — {reason}")
        _log_action(interaction.guild_id, "KICK", str(interaction.user), str(member), reason)

        embed = _mod_embed("MEMBER KICKED", member, interaction.user, reason, Colors.WARNING)
        await interaction.response.send_message(embed=embed)

    # ── /mute (timeout) ───────────────────────────────────────────────────────────

    @app_commands.command(name="mute", description="Timeout (mute) a member for a set duration.")
    @app_commands.describe(member="The member to mute", duration="Mute duration", reason="Reason")
    @app_commands.choices(duration=DURATION_CHOICES)
    async def mute(self, interaction: discord.Interaction,
                   member: discord.Member,
                   duration: str,
                   reason: Optional[str] = "No reason provided."):
        if not interaction.user.guild_permissions.moderate_members:
            return await _deny(interaction)
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await _deny(interaction, "You cannot mute someone with an equal or higher role.")
        if member == interaction.guild.me:
            return await _deny(interaction, "I cannot mute myself.")

        delta = DURATION_MAP.get(duration, timedelta(hours=1))
        until = datetime.now(timezone.utc) + delta

        await member.timeout(until, reason=f"{interaction.user} — {reason}")
        _log_action(interaction.guild_id, "MUTE", str(interaction.user), str(member), reason,
                    extra=f"Duration: {duration}")

        dm_embed = base_embed(
            "🔇  You have been muted",
            f"**Server:** {interaction.guild.name}\n**Duration:** {duration}\n**Reason:** {reason}",
            color=Colors.WARNING,
        )
        await _try_dm(member, dm_embed)

        embed = _mod_embed(
            "MEMBER MUTED",
            member, interaction.user, reason, Colors.WARNING,
            extra=f"Duration: `{duration}` — Expires: <t:{int(until.timestamp())}:R>",
        )
        await interaction.response.send_message(embed=embed)

    # ── /unmute ───────────────────────────────────────────────────────────────────

    @app_commands.command(name="unmute", description="Remove a timeout from a member.")
    @app_commands.describe(member="The member to unmute", reason="Reason")
    async def unmute(self, interaction: discord.Interaction,
                     member: discord.Member,
                     reason: Optional[str] = "No reason provided."):
        if not interaction.user.guild_permissions.moderate_members:
            return await _deny(interaction)

        if not member.is_timed_out():
            embed = warning_embed("NOT MUTED", f"{member.mention} is not currently muted.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await member.timeout(None, reason=f"{interaction.user} — {reason}")
        _log_action(interaction.guild_id, "UNMUTE", str(interaction.user), str(member), reason)

        embed = _mod_embed("MEMBER UNMUTED", member, interaction.user, reason, Colors.SUCCESS)
        await interaction.response.send_message(embed=embed)

    # ── /warn ─────────────────────────────────────────────────────────────────────

    @app_commands.command(name="warn", description="Issue a formal warning to a member.")
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    async def warn(self, interaction: discord.Interaction,
                   member: discord.Member,
                   reason: str):
        if not interaction.user.guild_permissions.moderate_members:
            return await _deny(interaction)
        if member.bot:
            embed = error_embed("INVALID TARGET", "You cannot warn a bot.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        total = _add_warning(
            interaction.guild_id, member.id, str(member),
            str(interaction.user), reason,
        )
        _log_action(interaction.guild_id, "WARN", str(interaction.user), str(member), reason,
                    extra=f"Total warnings: {total}")

        dm_embed = base_embed(
            f"⚠️  Warning Issued — {interaction.guild.name}",
            f"**Reason:** {reason}\n**Total warnings:** `{total}`",
            color=Colors.WARNING,
        )
        await _try_dm(member, dm_embed)

        embed = _mod_embed(
            "WARNING ISSUED",
            member, interaction.user, reason, Colors.WARNING,
            extra=f"Total warnings for this member: `{total}`",
        )
        await interaction.response.send_message(embed=embed)

    # ── /warnings ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="warnings", description="View the warning history of a member.")
    @app_commands.describe(member="The member to check")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.moderate_members:
            return await _deny(interaction)

        warns = _get_warnings(interaction.guild_id, member.id)

        if not warns:
            embed = success_embed(
                "NO WARNINGS",
                f"{member.mention} has a clean record. No warnings on file.",
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = base_embed(
            f"⚠️  Warning Record — {member.display_name}",
            f"Total warnings: `{len(warns)}`",
            color=Colors.WARNING,
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        for w in warns[-10:]:  # Show last 10
            ts = w.get("timestamp", "")[:10]
            embed.add_field(
                name=f"Warning #{w['id']}  —  {ts}",
                value=f"**Reason:** {w['reason']}\n**By:** {w['moderator']}",
                inline=False,
            )

        if len(warns) > 10:
            embed.set_footer(text=f"Showing last 10 of {len(warns)} warnings  •  COMMAND PROTOCOL")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /clearwarns ───────────────────────────────────────────────────────────────

    @app_commands.command(name="clearwarns", description="Clear all warnings for a member.")
    @app_commands.describe(member="The member whose warnings to clear")
    async def clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.administrator:
            return await _deny(interaction)

        warns = _get_warnings(interaction.guild_id, member.id)
        if not warns:
            embed = warning_embed("NO WARNINGS", f"{member.mention} has no warnings to clear.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        _clear_warnings(interaction.guild_id, member.id)
        _log_action(interaction.guild_id, "CLEARWARNS", str(interaction.user), str(member),
                    f"Cleared {len(warns)} warning(s)")

        embed = success_embed(
            "WARNINGS CLEARED",
            f"All `{len(warns)}` warning(s) for {member.mention} have been expunged from the record.",
        )
        await interaction.response.send_message(embed=embed)

    # ── /purge ────────────────────────────────────────────────────────────────────

    @app_commands.command(name="purge", description="Bulk delete messages in this channel.")
    @app_commands.describe(
        amount="Number of messages to delete (1–100)",
        member="Only delete messages from this member (optional)",
    )
    async def purge(self, interaction: discord.Interaction,
                    amount: app_commands.Range[int, 1, 100],
                    member: Optional[discord.Member] = None):
        if not interaction.user.guild_permissions.manage_messages:
            return await _deny(interaction)

        await interaction.response.defer(ephemeral=True)

        def check(msg):
            if member:
                return msg.author == member
            return True

        deleted = await interaction.channel.purge(limit=amount, check=check)
        _log_action(
            interaction.guild_id, "PURGE", str(interaction.user),
            str(interaction.channel),
            f"Deleted {len(deleted)} message(s)" + (f" from {member}" if member else ""),
        )

        target_str = f" from {member.mention}" if member else ""
        embed = success_embed(
            "CHANNEL PURGED",
            f"```\nOPERATION: PURGE\nCHANNEL: #{interaction.channel.name}\n"
            f"DELETED: {len(deleted)} message(s){(' — TARGET: ' + str(member)) if member else ''}\n"
            f"EXECUTED BY: {str(interaction.user).upper()}\n```",
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /lockdown ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="lockdown", description="Lock a channel — members cannot send messages.")
    @app_commands.describe(
        channel="Channel to lock (defaults to current)",
        reason="Reason for lockdown",
    )
    async def lockdown(self, interaction: discord.Interaction,
                       channel: Optional[discord.TextChannel] = None,
                       reason: Optional[str] = "No reason provided."):
        if not interaction.user.guild_permissions.manage_channels:
            return await _deny(interaction)

        target = channel or interaction.channel
        everyone = interaction.guild.default_role

        # Check if already locked
        overwrite = target.overwrites_for(everyone)
        if overwrite.send_messages is False:
            embed = warning_embed("ALREADY LOCKED", f"{target.mention} is already in lockdown.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        overwrite.send_messages = False
        await target.set_permissions(everyone, overwrite=overwrite,
                                     reason=f"{interaction.user} — {reason}")
        _log_action(interaction.guild_id, "LOCKDOWN", str(interaction.user),
                    f"#{target.name}", reason)

        embed = base_embed(
            f"🔒  CHANNEL LOCKED — #{target.name}",
            f"```\nSTATUS: LOCKDOWN ACTIVE\nCHANNEL: #{target.name}\nAUTHORIZED BY: {str(interaction.user).upper()}\n```\n\n"
            f"**Reason:** {reason}\n\nMembers can no longer send messages. Use `/unlock` to lift.",
            color=Colors.ERROR,
        )
        await interaction.response.send_message(embed=embed)

        # Also post a notice in the locked channel if it's different
        if target != interaction.channel:
            notice = base_embed(
                "🔒  CHANNEL LOCKED",
                f"This channel has been placed under lockdown.\n**Reason:** {reason}",
                color=Colors.ERROR,
            )
            await target.send(embed=notice)

    # ── /unlock ───────────────────────────────────────────────────────────────────

    @app_commands.command(name="unlock", description="Unlock a previously locked channel.")
    @app_commands.describe(
        channel="Channel to unlock (defaults to current)",
        reason="Reason for unlocking",
    )
    async def unlock(self, interaction: discord.Interaction,
                     channel: Optional[discord.TextChannel] = None,
                     reason: Optional[str] = "No reason provided."):
        if not interaction.user.guild_permissions.manage_channels:
            return await _deny(interaction)

        target = channel or interaction.channel
        everyone = interaction.guild.default_role

        overwrite = target.overwrites_for(everyone)
        if overwrite.send_messages is not False:
            embed = warning_embed("NOT LOCKED", f"{target.mention} is not currently locked.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        overwrite.send_messages = None  # Reset to inherit
        await target.set_permissions(everyone, overwrite=overwrite,
                                     reason=f"{interaction.user} — {reason}")
        _log_action(interaction.guild_id, "UNLOCK", str(interaction.user),
                    f"#{target.name}", reason)

        embed = base_embed(
            f"🔓  CHANNEL UNLOCKED — #{target.name}",
            f"```\nSTATUS: LOCKDOWN LIFTED\nCHANNEL: #{target.name}\nAUTHORIZED BY: {str(interaction.user).upper()}\n```\n\n"
            f"**Reason:** {reason}\n\nMembers may resume normal communications.",
            color=Colors.SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

        if target != interaction.channel:
            notice = base_embed(
                "🔓  CHANNEL UNLOCKED",
                f"This channel's lockdown has been lifted.\n**Reason:** {reason}",
                color=Colors.SUCCESS,
            )
            await target.send(embed=notice)

    # ── /slowmode ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="slowmode", description="Set slowmode delay on a channel.")
    @app_commands.describe(
        seconds="Slowmode delay in seconds (0 = disable)",
        channel="Target channel (defaults to current)",
    )
    @app_commands.choices(seconds=[
        app_commands.Choice(name="Off (0s)",    value=0),
        app_commands.Choice(name="5 seconds",   value=5),
        app_commands.Choice(name="10 seconds",  value=10),
        app_commands.Choice(name="30 seconds",  value=30),
        app_commands.Choice(name="1 minute",    value=60),
        app_commands.Choice(name="5 minutes",   value=300),
        app_commands.Choice(name="15 minutes",  value=900),
        app_commands.Choice(name="1 hour",      value=3600),
    ])
    async def slowmode(self, interaction: discord.Interaction,
                       seconds: int,
                       channel: Optional[discord.TextChannel] = None):
        if not interaction.user.guild_permissions.manage_channels:
            return await _deny(interaction)

        target = channel or interaction.channel
        await target.edit(slowmode_delay=seconds)
        _log_action(interaction.guild_id, "SLOWMODE", str(interaction.user),
                    f"#{target.name}", f"Set to {seconds}s")

        if seconds == 0:
            embed = success_embed(
                "SLOWMODE DISABLED",
                f"Slowmode has been **disabled** in {target.mention}.",
            )
        else:
            human = f"{seconds}s" if seconds < 60 else (f"{seconds//60}m" if seconds < 3600 else f"{seconds//3600}h")
            embed = base_embed(
                f"🐢  SLOWMODE SET — {human}",
                f"Slowmode set to `{human}` in {target.mention}.\nMembers must wait between messages.",
                color=Colors.WARNING,
            )
        await interaction.response.send_message(embed=embed)

    # ── /nick ─────────────────────────────────────────────────────────────────────

    @app_commands.command(name="nick", description="Force-change or reset a member's nickname.")
    @app_commands.describe(
        member="The target member",
        nickname="New nickname (leave empty to reset)",
    )
    async def nick(self, interaction: discord.Interaction,
                   member: discord.Member,
                   nickname: Optional[str] = None):
        if not interaction.user.guild_permissions.manage_nicknames:
            return await _deny(interaction)
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await _deny(interaction, "You cannot change the nickname of someone with an equal or higher role.")

        old_nick = member.display_name
        await member.edit(nick=nickname, reason=f"Nick change by {interaction.user}")
        _log_action(interaction.guild_id, "NICK", str(interaction.user), str(member),
                    f"{old_nick} → {nickname or '[reset]'}")

        if nickname:
            embed = success_embed(
                "NICKNAME CHANGED",
                f"{member.mention}'s nickname updated.\n`{old_nick}` → `{nickname}`",
            )
        else:
            embed = success_embed(
                "NICKNAME RESET",
                f"{member.mention}'s nickname has been reset to their username.",
            )
        await interaction.response.send_message(embed=embed)

    # ── /role ─────────────────────────────────────────────────────────────────────

    @app_commands.command(name="role", description="Add or remove a role from a member.")
    @app_commands.describe(
        member="The target member",
        role="The role to add or remove",
    )
    async def role(self, interaction: discord.Interaction,
                   member: discord.Member,
                   role: discord.Role):
        if not interaction.user.guild_permissions.manage_roles:
            return await _deny(interaction)
        if role >= interaction.guild.me.top_role:
            embed = error_embed("ROLE TOO HIGH", "I cannot manage a role that is above or equal to my own.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await _deny(interaction, "You cannot assign a role equal to or above your own.")

        if role in member.roles:
            await member.remove_roles(role, reason=f"Role removed by {interaction.user}")
            action = "removed from"
            color = Colors.WARNING
            _log_action(interaction.guild_id, "ROLE REMOVE", str(interaction.user),
                        str(member), f"Removed @{role.name}")
        else:
            await member.add_roles(role, reason=f"Role added by {interaction.user}")
            action = "added to"
            color = Colors.SUCCESS
            _log_action(interaction.guild_id, "ROLE ADD", str(interaction.user),
                        str(member), f"Added @{role.name}")

        embed = base_embed(
            f"🏷️  ROLE UPDATED",
            f"Role {role.mention} has been **{action}** {member.mention}.",
            color=color,
        )
        await interaction.response.send_message(embed=embed)

    # ── /modlog ───────────────────────────────────────────────────────────────────

    @app_commands.command(name="modlog", description="View recent moderation actions in this server.")
    @app_commands.describe(limit="Number of entries to show (default 10, max 15)")
    async def modlog(self, interaction: discord.Interaction,
                     limit: app_commands.Range[int, 1, 15] = 10):
        if not interaction.user.guild_permissions.moderate_members:
            return await _deny(interaction)

        entries = _get_modlog(interaction.guild_id, limit)

        if not entries:
            embed = base_embed(
                "📋  MODERATION LOG",
                "No moderation actions have been recorded yet.",
                color=Colors.NEUTRAL,
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        action_icons = {
            "BAN": "⛔", "UNBAN": "✅", "KICK": "🥾", "MUTE": "🔇",
            "UNMUTE": "🔊", "WARN": "⚠️", "CLEARWARNS": "🗑️",
            "PURGE": "🧹", "LOCKDOWN": "🔒", "UNLOCK": "🔓",
            "SLOWMODE": "🐢", "NICK": "✏️", "ROLE ADD": "➕",
            "ROLE REMOVE": "➖",
        }

        embed = base_embed(
            f"📋  MODERATION LOG — Last {len(entries)} Actions",
            f"```\nSERVER: {interaction.guild.name}\nCLEARANCE: MODERATOR\n```",
            color=Colors.ADMIN,
        )

        for entry in reversed(entries):
            icon = action_icons.get(entry["action"], "•")
            ts = entry.get("timestamp", "")[:10]
            value = f"**Target:** {entry['target']}\n**By:** {entry['moderator']}\n**Reason:** {entry['reason']}"
            if entry.get("extra"):
                value += f"\n**Detail:** {entry['extra']}"
            embed.add_field(
                name=f"{icon}  {entry['action']}  —  {ts}",
                value=value,
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
