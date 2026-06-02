"""
Information Cog — /about, /roadmap, /progress, /status, /devlog, /changelog
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

from utils.embeds import (
    base_embed, info_embed, success_embed,
    Colors, SIGNAL_ICON, STAR_ICON,
)

log = logging.getLogger("CommandProtocol.Information")

STATUS_ICONS = {"complete": "✅", "active": "🔶", "upcoming": "⬜"}


class InformationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dm = bot.data_manager

    # ── /about ────────────────────────────────────────────────────────────────

    @app_commands.command(name="about", description="Learn about Command Protocol.")
    async def about(self, interaction: discord.Interaction):
        info = self.dm.get_game_info()

        embed = base_embed(
            "COMMAND PROTOCOL — CLASSIFIED BRIEFING",
            (
                "```\nINCOMING TRANSMISSION — PRIORITY ALPHA\n"
                "CLEARANCE: PUBLIC\nSOURCE: COMMAND TERMINAL\n```\n\n"
                f"{info.get('description', 'No data.')}"
            ),
            color=Colors.PRIMARY,
        )
        embed.add_field(name="🕹️  Genre",    value=info.get("genre", "—"),     inline=True)
        embed.add_field(name="💻  Platform", value=info.get("platform", "—"),  inline=True)
        embed.add_field(name="📊  Status",   value=info.get("status", "—"),    inline=True)
        embed.add_field(name="🔢  Version",  value=info.get("version", "—"),   inline=True)
        embed.add_field(name="👨‍💻  Developer", value=info.get("developer", "—"), inline=True)
        embed.add_field(
            name="🗂️  Quick Links",
            value="Use `/roadmap`, `/progress`, `/devlog`, or `/changelog` for more details.",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    # ── /roadmap ──────────────────────────────────────────────────────────────

    @app_commands.command(name="roadmap", description="View the Command Protocol development roadmap.")
    async def roadmap(self, interaction: discord.Interaction):
        data = self.dm.get_roadmap()
        phases = data.get("phases", [])

        embed = base_embed(
            f"{SIGNAL_ICON}  DEVELOPMENT ROADMAP",
            "```\nCOMMAND PROTOCOL — MISSION BRIEFING\nCLASSIFICATION: DEVELOPMENT INTEL\n```",
            color=Colors.PRIMARY,
        )

        for phase in phases:
            icon = STATUS_ICONS.get(phase.get("status", "upcoming"), "⬜")
            status_label = phase.get("status", "upcoming").upper()
            items_text = "\n".join(f"• {item}" for item in phase.get("items", []))

            embed.add_field(
                name=f"{icon}  {phase['name']}  —  `{status_label}`",
                value=items_text or "No items listed.",
                inline=False,
            )

        embed.set_footer(text="✅ Complete  🔶 Active  ⬜ Upcoming  •  COMMAND PROTOCOL")
        await interaction.response.send_message(embed=embed)

    # ── /progress ─────────────────────────────────────────────────────────────

    @app_commands.command(name="progress", description="View overall development progress and system completion.")
    async def progress(self, interaction: discord.Interaction):
        data = self.dm.get_progress()

        pct = data.get("overall_percent", 0)
        filled = round(pct / 5)   # 20-block bar
        bar = "█" * filled + "░" * (20 - filled)

        embed = base_embed(
            "📊  DEVELOPMENT PROGRESS REPORT",
            (
                f"```\n{bar}  {pct}%\n"
                f"OVERALL COMPLETION\n```\n\n"
                f"**Version:** `{data.get('version', '—')}`\n"
                f"**Current Objective:** {data.get('current_objective', '—')}"
            ),
            color=Colors.SUCCESS if pct >= 50 else Colors.PRIMARY,
        )

        completed = data.get("completed", [])
        if completed:
            embed.add_field(
                name="✅  Completed Systems",
                value="\n".join(f"• {s}" for s in completed),
                inline=False,
            )

        in_progress = data.get("in_progress", [])
        if in_progress:
            embed.add_field(
                name="🔶  Systems in Progress",
                value="\n".join(f"• {s}" for s in in_progress),
                inline=False,
            )

        upcoming = data.get("upcoming", [])
        if upcoming:
            embed.add_field(
                name="⬜  Upcoming Systems",
                value="\n".join(f"• {s}" for s in upcoming),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    # ── /status ───────────────────────────────────────────────────────────────

    @app_commands.command(name="status", description="View current build version, active objectives, and system status.")
    async def status(self, interaction: discord.Interaction):
        info = self.dm.get_game_info()
        progress = self.dm.get_progress()

        pct = progress.get("overall_percent", 0)
        filled = round(pct / 5)
        bar = "█" * filled + "░" * (20 - filled)

        in_progress = progress.get("in_progress", [])
        completed = progress.get("completed", [])

        embed = base_embed(
            "🖥️  COMMAND PROTOCOL — SYSTEM STATUS",
            "```\nTERMINAL UPLINK: ACTIVE\nDATA FEED: LIVE\nCLEARANCE: PUBLIC\n```",
            color=Colors.PRIMARY,
        )
        embed.add_field(name="🔢  Version",         value=f"`{info.get('version', '—')}`",       inline=True)
        embed.add_field(name="📊  Build Status",    value=info.get("status", "—"),               inline=True)
        embed.add_field(name="🌐  Platform",        value=info.get("platform", "—"),             inline=True)
        embed.add_field(
            name="📈  Overall Progress",
            value=f"```{bar}  {pct}%```",
            inline=False,
        )
        embed.add_field(
            name="🎯  Current Objective",
            value=progress.get("current_objective", "No active objective."),
            inline=False,
        )
        embed.add_field(
            name="🔶  Active Systems",
            value="\n".join(f"• {s}" for s in in_progress) or "None active.",
            inline=True,
        )
        embed.add_field(
            name=f"✅  Completed Systems",
            value=f"`{len(completed)}` systems online",
            inline=True,
        )
        await interaction.response.send_message(embed=embed)

    # ── /devlog ───────────────────────────────────────────────────────────────

    @app_commands.command(name="devlog", description="Read the latest developer log.")
    async def devlog(self, interaction: discord.Interaction):
        data = self.dm.get_devlog()

        embed = base_embed(
            f"📋  DEV LOG — {data.get('title', 'Untitled')}",
            (
                f"```\nSOURCE: {data.get('author', 'Dev Team').upper()}\n"
                f"DATE: {data.get('date', '—')}\n"
                f"CLASSIFICATION: DEVELOPMENT UPDATE\n```\n\n"
                f"{data.get('content', 'No log entry available.')}"
            ),
            color=Colors.NEUTRAL,
        )
        await interaction.response.send_message(embed=embed)

    # ── /changelog ────────────────────────────────────────────────────────────

    @app_commands.command(name="changelog", description="View the latest update notes and patch changes.")
    async def changelog(self, interaction: discord.Interaction):
        data = self.dm.get_changelog()

        embed = base_embed(
            f"📝  CHANGELOG — {data.get('version', '—')}",
            (
                f"```\nRELEASE: {data.get('version', '—')}\n"
                f"DATE: {data.get('date', '—')}\n"
                f"COMPILED BY: {data.get('author', 'Dev Team').upper()}\n```\n\n"
                f"{data.get('notes', 'No changelog available.')}"
            ),
            color=Colors.NEUTRAL,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(InformationCog(bot))
