"""
Admin Cog — privileged commands for updating game data and announcements.
All commands are admin-only and use Discord modals for clean input.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

from utils.embeds import (
    base_embed, admin_embed, success_embed, error_embed,
    Colors,
)
from utils.checks import is_admin, send_permission_error

log = logging.getLogger("CommandProtocol.Admin")


# ─── Update Devlog Modal ────────────────────────────────────────────────────────

class UpdateDevlogModal(discord.ui.Modal, title="Update Dev Log"):
    log_title = discord.ui.TextInput(
        label="Log Title",
        placeholder="e.g. Combat System — First Strike",
        max_length=100,
        required=True,
    )
    content = discord.ui.TextInput(
        label="Log Content",
        placeholder="Use • for bullet points...",
        style=discord.TextStyle.long,
        max_length=2000,
        required=True,
    )

    def __init__(self, dm):
        super().__init__()
        self.dm = dm

    async def on_submit(self, interaction: discord.Interaction):
        success = self.dm.update_devlog(
            title=str(self.log_title),
            content=str(self.content),
            author=str(interaction.user),
        )
        if success:
            embed = success_embed(
                "DEV LOG UPDATED",
                f"```\nOPERATION: DEVLOG UPDATE\nSTATUS: SUCCESS\nOPERATOR: {str(interaction.user).upper()}\n```\n\n"
                f"**New Title:** {str(self.log_title)}\n\n"
                f"Use `/devlog` to verify the update.",
            )
        else:
            embed = error_embed("UPDATE FAILED", "Failed to write devlog data. Check server logs.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── Update Changelog Modal ─────────────────────────────────────────────────────

class UpdateChangelogModal(discord.ui.Modal, title="Update Changelog"):
    version = discord.ui.TextInput(
        label="Version",
        placeholder="e.g. v0.5.0-alpha",
        max_length=30,
        required=True,
    )
    notes = discord.ui.TextInput(
        label="Changelog Notes",
        placeholder="**New:**\n• ...\n\n**Fixed:**\n• ...\n\n**Known Issues:**\n• ...",
        style=discord.TextStyle.long,
        max_length=2000,
        required=True,
    )

    def __init__(self, dm):
        super().__init__()
        self.dm = dm

    async def on_submit(self, interaction: discord.Interaction):
        success = self.dm.update_changelog(
            version=str(self.version),
            notes=str(self.notes),
            author=str(interaction.user),
        )
        if success:
            embed = success_embed(
                "CHANGELOG UPDATED",
                f"```\nOPERATION: CHANGELOG UPDATE\nVERSION: {str(self.version)}\nSTATUS: SUCCESS\n```\n\n"
                f"Use `/changelog` to verify.",
            )
        else:
            embed = error_embed("UPDATE FAILED", "Failed to write changelog data.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── Progress Section Modals ────────────────────────────────────────────────────

class ProgressGeneralModal(discord.ui.Modal, title="Update — General Info"):
    version = discord.ui.TextInput(
        label="Version",
        placeholder="e.g. v0.5.0-alpha",
        max_length=30,
        required=True,
    )
    overall_percent = discord.ui.TextInput(
        label="Overall Completion % (0–100)",
        placeholder="e.g. 35",
        max_length=3,
        required=True,
    )
    objective = discord.ui.TextInput(
        label="Current Objective",
        placeholder="e.g. Complete combat loop and begin balance testing",
        max_length=200,
        required=True,
    )

    def __init__(self, dm, existing: dict):
        super().__init__()
        self.dm = dm
        self.version.default = existing.get("version", "")
        self.overall_percent.default = str(existing.get("overall_percent", ""))
        self.objective.default = existing.get("current_objective", "")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pct = int(str(self.overall_percent).strip())
            pct = max(0, min(100, pct))
        except ValueError:
            return await interaction.response.send_message(
                embed=error_embed("INVALID INPUT", "Overall percent must be a number between 0 and 100."),
                ephemeral=True,
            )

        existing = self.dm.get_progress()
        existing["version"] = str(self.version).strip()
        existing["current_objective"] = str(self.objective).strip()
        existing["overall_percent"] = pct

        if self.dm.update_progress(existing):
            await interaction.response.send_message(
                embed=success_embed(
                    "PROGRESS UPDATED — GENERAL",
                    f"```\nVERSION: {existing['version']}\nCOMPLETION: {pct}%\nSTATUS: SUCCESS\n```\n\nUse `/progress` to verify.",
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=error_embed("UPDATE FAILED", "Failed to write progress data."),
                ephemeral=True,
            )


class ProgressCompletedModal(discord.ui.Modal, title="Update — Completed Systems"):
    completed = discord.ui.TextInput(
        label="Completed Systems (one per line)",
        placeholder="Project scaffolding & engine setup\nCore movement & pathfinding engine",
        style=discord.TextStyle.long,
        required=False,
        max_length=1000,
    )

    def __init__(self, dm, existing: dict):
        super().__init__()
        self.dm = dm
        self.completed.default = "\n".join(existing.get("completed", []))

    async def on_submit(self, interaction: discord.Interaction):
        existing = self.dm.get_progress()
        raw = str(self.completed).strip()
        existing["completed"] = [line.strip() for line in raw.splitlines() if line.strip()]

        if self.dm.update_progress(existing):
            count = len(existing["completed"])
            await interaction.response.send_message(
                embed=success_embed(
                    "PROGRESS UPDATED — COMPLETED",
                    f"```\nSYSTEMS LOGGED: {count}\nSTATUS: SUCCESS\n```\n\nUse `/progress` to verify.",
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=error_embed("UPDATE FAILED", "Failed to write progress data."),
                ephemeral=True,
            )


class ProgressInProgressModal(discord.ui.Modal, title="Update — Systems In Progress"):
    in_progress = discord.ui.TextInput(
        label="In-Progress Systems (one per line, include %)",
        placeholder="Combat system 20%\nFog of war 40%",
        style=discord.TextStyle.long,
        required=False,
        max_length=800,
    )

    def __init__(self, dm, existing: dict):
        super().__init__()
        self.dm = dm
        self.in_progress.default = "\n".join(existing.get("in_progress", []))

    async def on_submit(self, interaction: discord.Interaction):
        existing = self.dm.get_progress()
        raw = str(self.in_progress).strip()
        existing["in_progress"] = [line.strip() for line in raw.splitlines() if line.strip()]

        if self.dm.update_progress(existing):
            count = len(existing["in_progress"])
            await interaction.response.send_message(
                embed=success_embed(
                    "PROGRESS UPDATED — IN PROGRESS",
                    f"```\nACTIVE SYSTEMS: {count}\nSTATUS: SUCCESS\n```\n\nUse `/progress` to verify.",
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=error_embed("UPDATE FAILED", "Failed to write progress data."),
                ephemeral=True,
            )


class ProgressUpcomingModal(discord.ui.Modal, title="Update — Upcoming Systems"):
    upcoming = discord.ui.TextInput(
        label="Upcoming Systems (one per line)",
        placeholder="Multiplayer networking layer\nCampaign mode — Chapter 1",
        style=discord.TextStyle.long,
        required=False,
        max_length=800,
    )

    def __init__(self, dm, existing: dict):
        super().__init__()
        self.dm = dm
        self.upcoming.default = "\n".join(existing.get("upcoming", []))

    async def on_submit(self, interaction: discord.Interaction):
        existing = self.dm.get_progress()
        raw = str(self.upcoming).strip()
        existing["upcoming"] = [line.strip() for line in raw.splitlines() if line.strip()]

        if self.dm.update_progress(existing):
            count = len(existing["upcoming"])
            await interaction.response.send_message(
                embed=success_embed(
                    "PROGRESS UPDATED — UPCOMING",
                    f"```\nQUEUED SYSTEMS: {count}\nSTATUS: SUCCESS\n```\n\nUse `/progress` to verify.",
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=error_embed("UPDATE FAILED", "Failed to write progress data."),
                ephemeral=True,
            )


# ─── Progress Section Select View ───────────────────────────────────────────────

class ProgressSectionSelect(discord.ui.Select):
    def __init__(self, dm):
        self.dm = dm
        options = [
            discord.SelectOption(
                label="General Info",
                value="general",
                description="Version, completion %, current objective",
                emoji="📊",
            ),
            discord.SelectOption(
                label="Completed Systems",
                value="completed",
                description="Edit the list of finished systems",
                emoji="✅",
            ),
            discord.SelectOption(
                label="Systems In Progress",
                value="in_progress",
                description="Edit active systems and their percentages",
                emoji="🔶",
            ),
            discord.SelectOption(
                label="Upcoming Systems",
                value="upcoming",
                description="Edit the backlog of future systems",
                emoji="⬜",
            ),
        ]
        super().__init__(
            placeholder="Select a section to edit...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        existing = self.dm.get_progress()
        section = self.values[0]

        modal_map = {
            "general":     ProgressGeneralModal,
            "completed":   ProgressCompletedModal,
            "in_progress": ProgressInProgressModal,
            "upcoming":    ProgressUpcomingModal,
        }

        modal = modal_map[section](self.dm, existing)
        await interaction.response.send_modal(modal)


class ProgressSectionView(discord.ui.View):
    def __init__(self, dm):
        super().__init__(timeout=60)
        self.add_item(ProgressSectionSelect(dm))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


# ─── Update About Modal ─────────────────────────────────────────────────────────
# Split into two modals since Discord caps modals at 5 fields and game_info has 6.

# ─── Update About Modal ─────────────────────────────────────────────────────────

class UpdateAboutModal(discord.ui.Modal, title="Update About Game Info"):
    name = discord.ui.TextInput(
        label="Game Name & Tagline",
        placeholder="e.g. Command Protocol | Wage war. Control the field.",
        max_length=150,
        required=True,
    )
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Full game description shown in /about...",
        style=discord.TextStyle.long,
        max_length=1500,
        required=True,
    )
    status_version = discord.ui.TextInput(
        label="Status & Version (Format: Status | Version)",
        placeholder="e.g. In Development — Alpha Phase | v0.4.2-alpha",
        max_length=120,
        required=True,
    )
    meta_info = discord.ui.TextInput(
        label="Genre, Platform, Developer (Comma Separated)",
        placeholder="e.g. Real-Time Strategy, PC (Windows), Dev Team Name",
        max_length=200,
        required=True,
    )

    def __init__(self, dm):
        super().__init__()
        self.dm = dm
        existing = dm.get_game_info()

        # Pre-filling with structured strings from existing JSON data
        self.name.default = f"{existing.get('name', '')} | {existing.get('tagline', '')}".strip(" |")
        self.description.default = existing.get("description", "")[:1500]
        self.status_version.default = f"{existing.get('status', '')} | {existing.get('version', '')}".strip(" |")

        meta_list = [existing.get("genre", ""), existing.get("platform", ""), existing.get("developer", "")]
        self.meta_info.default = ", ".join([i for i in meta_list if i])

    async def on_submit(self, interaction: discord.Interaction):
        # Parse split inputs safely
        name_part = str(self.name).split("|", 1)
        status_part = str(self.status_version).split("|", 1)
        meta_parts = str(self.meta_info).split(",")

        # Extract values or fallback safely
        name = name_part[0].strip()
        tagline = name_part[1].strip() if len(name_part) > 1 else ""

        status = status_part[0].strip()
        version = status_part[1].strip() if len(status_part) > 1 else ""

        genre = meta_parts[0].strip() if len(meta_parts) > 0 else ""
        platform = meta_parts[1].strip() if len(meta_parts) > 1 else ""
        developer = meta_parts[2].strip() if len(meta_parts) > 2 else ""

        new_data = {
            "name": name,
            "tagline": tagline,
            "description": str(self.description).strip(),
            "status": status,
            "version": version,
            "genre": genre,
            "platform": platform,
            "developer": developer,
        }

        from pathlib import Path
        import json
        data_path = Path(__file__).parent.parent / "data" / "game_info.json"

        try:
            data_path.parent.mkdir(exist_ok=True)
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)
            ok = True
        except Exception as e:
            log.error(f"Failed to write game_info.json: {e}")
            ok = False
        if ok:
            await interaction.response.send_message(
                embed=success_embed(
                    "ABOUT UPDATED",
                    "Game information updated successfully."
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=error_embed(
                    "UPDATE FAILED",
                    "Failed to save game information."
                ),
                ephemeral=True
            )


class AnnounceModal(discord.ui.Modal, title="Post an Announcement"):
    title_field = discord.ui.TextInput(
        label="Announcement Title",
        placeholder="e.g. ALPHA 0.5 DEPLOYMENT INCOMING",
        max_length=100,
        required=True,
    )
    message = discord.ui.TextInput(
        label="Announcement Body",
        placeholder="Write your announcement here...",
        style=discord.TextStyle.long,
        max_length=2000,
        required=True,
    )
    ping = discord.ui.TextInput(
        label="Ping Role? (type role name or leave blank)",
        placeholder="e.g. everyone  or  Commanders  or leave blank",
        required=False,
        max_length=50,
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        channel_id = self.bot.config.get_int("ANNOUNCE_CHANNEL_ID")

        embed = base_embed(
            f"📢  {str(self.title_field).upper()}",
            str(self.message),
            color=Colors.WARNING,
        )
        embed.set_author(
            name=f"Posted by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.set_footer(text="Official Announcement  •  COMMAND PROTOCOL")

        ping_text = ""
        ping_input = str(self.ping).strip().lower()
        if ping_input:
            if ping_input in ("everyone", "@everyone"):
                ping_text = "@everyone "
            elif ping_input in ("here", "@here"):
                ping_text = "@here "
            else:
                role = discord.utils.find(
                    lambda r: r.name.lower() == ping_input,
                    interaction.guild.roles,
                )
                if role:
                    ping_text = f"{role.mention} "

        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                await channel.send(content=ping_text or None, embed=embed)
                confirm = success_embed(
                    "ANNOUNCEMENT BROADCAST",
                    f"Message transmitted to {channel.mention}.",
                )
                return await interaction.response.send_message(embed=confirm, ephemeral=True)

        # Fallback: send in current channel
        await interaction.response.send_message(content=ping_text or None, embed=embed)


# ─── Admin Cog ──────────────────────────────────────────────────────────────────

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dm = bot.data_manager

    async def _check_admin(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        admin_role_ids = [int(rid) for rid in self.bot.config.get_list("ADMIN_ROLE_IDS") if rid]
        user_role_ids = [role.id for role in interaction.user.roles]
        if any(rid in user_role_ids for rid in admin_role_ids):
            return True
        await send_permission_error(interaction)
        return False

    @app_commands.command(name="updatedevlog", description="[ADMIN] Update the latest dev log entry.")
    async def updatedevlog(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return
        modal = UpdateDevlogModal(self.dm)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="updatechangelog", description="[ADMIN] Update the latest changelog entry.")
    async def updatechangelog(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return
        modal = UpdateChangelogModal(self.dm)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="updateprogress", description="[ADMIN] Update the development progress data.")
    async def updateprogress(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return

        embed = base_embed(
            "📊  UPDATE PROGRESS — SELECT SECTION",
            "```\nOPERATION: PROGRESS EDIT\nCLEARANCE: ADMIN\n```\n\n"
            "Choose which section you want to edit. "
            "The modal will open pre-filled with the current values.",
            color=Colors.PRIMARY,
        )
        view = ProgressSectionView(self.dm)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="updateabout", description="[ADMIN] Update the /about game information page.")
    async def updateabout(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return
        modal = UpdateAboutModal(self.dm)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="announce", description="[ADMIN] Post an official announcement.")
    async def announce(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return
        modal = AnnounceModal(self.bot)
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))