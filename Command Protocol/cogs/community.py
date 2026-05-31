"""
Community Cog — /suggest and /bugreport with Discord modals for form input.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

from utils.embeds import (
    base_embed, success_embed, error_embed, warning_embed,
    Colors,
)

log = logging.getLogger("CommandProtocol.Community")


# ─── Suggestion Modal ───────────────────────────────────────────────────────────

class SuggestionModal(discord.ui.Modal, title="Submit a Suggestion"):
    suggestion = discord.ui.TextInput(
        label="Your Suggestion",
        placeholder="Describe your idea for Command Protocol...",
        style=discord.TextStyle.long,
        min_length=20,
        max_length=1000,
        required=True,
    )
    context = discord.ui.TextInput(
        label="Additional Context (optional)",
        placeholder="Why would this improve the game? Any references?",
        style=discord.TextStyle.long,
        required=False,
        max_length=500,
    )

    def __init__(self, dm):
        super().__init__()
        self.dm = dm

    async def on_submit(self, interaction: discord.Interaction):
        full_suggestion = str(self.suggestion)
        extra = str(self.context).strip()
        if extra:
            full_suggestion += f"\n\n**Additional context:** {extra}"

        suggestion_id = self.dm.add_suggestion(
            user_id=interaction.user.id,
            username=str(interaction.user),
            suggestion=full_suggestion,
        )

        embed = success_embed(
            "SUGGESTION RECEIVED",
            (
                f"```\nINTEL REPORT #{suggestion_id:04d} LOGGED\n"
                f"SUBMITTED BY: {interaction.user.display_name.upper()}\n"
                f"STATUS: PENDING REVIEW\n```\n\n"
                f"**Your suggestion:**\n{str(self.suggestion)}"
            ),
        )
        embed.set_footer(text=f"Suggestion #{suggestion_id:04d}  •  COMMAND PROTOCOL")

        # Post to suggestion channel if configured
        channel_id = interaction.client.config.get_int("SUGGESTION_CHANNEL_ID")
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                channel_embed = base_embed(
                    f"💡  NEW SUGGESTION — #{suggestion_id:04d}",
                    full_suggestion,
                    color=Colors.PRIMARY,
                )
                channel_embed.set_author(
                    name=str(interaction.user),
                    icon_url=interaction.user.display_avatar.url,
                )
                channel_embed.add_field(name="User ID", value=str(interaction.user.id), inline=True)
                channel_embed.add_field(name="Suggestion #", value=f"`{suggestion_id:04d}`", inline=True)
                await channel.send(embed=channel_embed)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        log.error(f"Suggestion modal error: {error}")
        embed = error_embed("SUBMISSION FAILED", "An error occurred. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── Bug Report Modal ───────────────────────────────────────────────────────────

class BugReportModal(discord.ui.Modal, title="Submit a Bug Report"):
    title_field = discord.ui.TextInput(
        label="Bug Title",
        placeholder="Short descriptive title (e.g. 'Units freeze on map edge')",
        max_length=100,
        required=True,
    )
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Describe the bug in detail...",
        style=discord.TextStyle.long,
        min_length=20,
        max_length=800,
        required=True,
    )
    steps = discord.ui.TextInput(
        label="Steps to Reproduce",
        placeholder="1. Load map\n2. Select unit\n3. Bug occurs...",
        style=discord.TextStyle.long,
        required=False,
        max_length=400,
    )
    severity = discord.ui.TextInput(
        label="Severity (Low / Medium / High / Critical)",
        placeholder="Low / Medium / High / Critical",
        max_length=20,
        required=True,
    )

    def __init__(self, dm):
        super().__init__()
        self.dm = dm

    async def on_submit(self, interaction: discord.Interaction):
        severity_raw = str(self.severity).strip().title()
        valid_severities = {"Low", "Medium", "High", "Critical"}
        if severity_raw not in valid_severities:
            severity_raw = "Medium"  # Default fallback

        severity_colors = {
            "Low": Colors.SUCCESS,
            "Medium": Colors.WARNING,
            "High": Colors.ERROR,
            "Critical": 0xFF0000,
        }
        color = severity_colors.get(severity_raw, Colors.WARNING)

        report_id = self.dm.add_bug_report(
            user_id=interaction.user.id,
            username=str(interaction.user),
            title=str(self.title_field),
            description=str(self.description),
            steps=str(self.steps) or "Not provided.",
            severity=severity_raw,
        )

        embed = base_embed(
            f"🐛  BUG REPORT #{report_id:04d} LOGGED",
            (
                f"```\nREPORT #{report_id:04d}\n"
                f"SEVERITY: {severity_raw.upper()}\n"
                f"STATUS: OPEN\n```\n\n"
                f"**{str(self.title_field)}**\n{str(self.description)}"
            ),
            color=color,
        )
        embed.set_footer(text=f"Bug Report #{report_id:04d}  •  COMMAND PROTOCOL")

        # Post to bug report channel if configured
        channel_id = interaction.client.config.get_int("BUGREPORT_CHANNEL_ID")
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                channel_embed = base_embed(
                    f"🐛  BUG REPORT #{report_id:04d}  —  `{severity_raw.upper()}`",
                    str(self.description),
                    color=color,
                )
                channel_embed.set_author(
                    name=str(interaction.user),
                    icon_url=interaction.user.display_avatar.url,
                )
                channel_embed.add_field(name="Title", value=str(self.title_field), inline=False)
                channel_embed.add_field(
                    name="Steps to Reproduce",
                    value=str(self.steps) or "Not provided.",
                    inline=False,
                )
                channel_embed.add_field(name="Severity",     value=f"`{severity_raw}`",      inline=True)
                channel_embed.add_field(name="Report #",     value=f"`{report_id:04d}`",     inline=True)
                channel_embed.add_field(name="Reporter ID",  value=str(interaction.user.id), inline=True)
                await channel.send(embed=channel_embed)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        log.error(f"Bug report modal error: {error}")
        embed = error_embed("SUBMISSION FAILED", "An error occurred. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── Community Cog ──────────────────────────────────────────────────────────────

class CommunityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dm = bot.data_manager

    @app_commands.command(name="suggest", description="Submit a suggestion or feature request for Command Protocol.")
    async def suggest(self, interaction: discord.Interaction):
        modal = SuggestionModal(self.dm)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="bugreport", description="Report a bug or issue found in Command Protocol.")
    async def bugreport(self, interaction: discord.Interaction):
        modal = BugReportModal(self.dm)
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(CommunityCog(bot))
