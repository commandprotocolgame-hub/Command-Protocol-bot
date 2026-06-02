"""
Faction Cog — handles /join, /army, /rebels, /switchside commands.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

from utils.embeds import (
    base_embed, army_embed, rebels_embed,
    success_embed, error_embed, warning_embed,
    Colors, ARMY_ICON, REBELS_ICON,
)

log = logging.getLogger("CommandProtocol.Faction")


class FactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    def _get_role(self, guild: discord.Guild, key: str) -> discord.Role | None:
        role_id = self.config.get_int(key)
        if not role_id:
            return None
        return guild.get_role(role_id)

    async def _assign_faction(
        self,
        interaction: discord.Interaction,
        faction: str,  # "army" or "rebels"
    ):
        await interaction.response.defer(ephemeral=False)

        guild = interaction.guild
        member = interaction.user

        if faction == "army":
            join_key = "ARMY_ROLE_ID"
            remove_key = "REBELS_ROLE_ID"
        else:
            join_key = "REBELS_ROLE_ID"
            remove_key = "ARMY_ROLE_ID"

        join_role = self._get_role(guild, join_key)
        remove_role = self._get_role(guild, remove_key)

        # Check role configuration
        if not join_role:
            embed = error_embed(
                "ROLE NOT CONFIGURED",
                f"The `{faction.upper()}` role ID has not been set in `config.json`.\n"
                "Contact an admin to configure faction roles.",
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Check if already in this faction
        if join_role in member.roles:
            embed = warning_embed(
                "ALREADY ENLISTED",
                f"You are already registered with **{'The Army' if faction == 'army' else 'The Rebel Movement'}**, soldier.\n"
                "No re-enlistment required.",
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Remove opposite faction role
        try:
            if remove_role and remove_role in member.roles:
                await member.remove_roles(remove_role, reason="Faction switch via /join")
        except discord.Forbidden:
            embed = error_embed(
                "PERMISSIONS ERROR",
                "I lack the permissions to manage roles. Contact an admin.",
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Assign new faction role
        try:
            await member.add_roles(join_role, reason=f"Joined {faction} via /join")
        except discord.Forbidden:
            embed = error_embed(
                "PERMISSIONS ERROR",
                "I lack the permissions to assign roles. Contact an admin.",
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Build confirmation embed
        if faction == "army":
            embed = army_embed(
                "ENLISTMENT CONFIRMED — THE ARMY",
                f"```\nWELCOME, COMMANDER.\nIdentification: {member.display_name}\nStatus: ACTIVE DUTY\nClearance: STANDARD\n```\n"
                f"You have been officially enlisted into **The Army**.\n\n"
                f"Follow orders. Protect the chain of command. Crush resistance.\n\n"
                f"> *\"Discipline is the bridge between goals and accomplishment.\"*",
            )
            embed.set_thumbnail(url="https://i.imgur.com/placeholder_army.png")
        else:
            embed = rebels_embed(
                "INITIATION COMPLETE — REBEL MOVEMENT",
                f"```\nWELCOME, OPERATIVE.\nCodename: {member.display_name}\nStatus: FIELD ACTIVE\nNetwork: ENCRYPTED\n```\n"
                f"You have joined **The Rebel Movement**.\n\n"
                f"Operate in shadows. Strike fast. Never surrender.\n\n"
                f"> *\"They have the guns, but we have the numbers.\"*",
            )
            embed.set_thumbnail(url="https://i.imgur.com/placeholder_rebel.png")

        await interaction.followup.send(embed=embed)

    # ── /join ──────────────────────────────────────────────────────────────────

    faction_group = app_commands.Group(
        name="join",
        description="Enlist in a faction."
    )

    @faction_group.command(name="army", description="Enlist in The Army — disciplined, powerful, organized.")
    async def join_army(self, interaction: discord.Interaction):
        await self._assign_faction(interaction, "army")

    @faction_group.command(name="rebels", description="Join the Rebel Movement — free, unpredictable, dangerous.")
    async def join_rebels(self, interaction: discord.Interaction):
        await self._assign_faction(interaction, "rebels")

    # ── /army (lore) ──────────────────────────────────────────────────────────

    @app_commands.command(name="army", description="View The Army faction — lore, goals, and strengths.")
    async def army_info(self, interaction: discord.Interaction):
        embed = army_embed(
            "THE ARMY — FACTION DOSSIER",
            (
                "```\nCLASSIFICATION: PUBLIC RECORD\n"
                "FACTION CODE: ALPHA-1\nSTATUS: OPERATIONAL\n```\n\n"
                "**Overview**\n"
                "The Army is the last remnant of centralized military power on Earth. "
                "Forged from the ashes of collapsed nation-states, it operates on iron discipline, "
                "advanced logistics, and overwhelming firepower. Where others see chaos, The Army sees "
                "an opportunity to restore order — by any means necessary.\n"
            ),
        )
        embed.add_field(
            name=f"{ARMY_ICON}  Doctrine",
            value=(
                "Overwhelming force. Superior numbers. Coordinated assault.\n"
                "The Army doesn't fight battles — it *ends* them."
            ),
            inline=False,
        )
        embed.add_field(
            name="⚔️  Strengths",
            value=(
                "• Heavy armor & siege units\n"
                "• Advanced supply chains\n"
                "• Fortified base defenses\n"
                "• Air superiority capabilities"
            ),
            inline=True,
        )
        embed.add_field(
            name="🎯  Strategic Goals",
            value=(
                "• Establish unified global command\n"
                "• Eradicate rebel insurgency\n"
                "• Secure all resource nodes\n"
                "• Restore the old order"
            ),
            inline=True,
        )
        embed.add_field(
            name="📻  Command Broadcast",
            value=(
                "> *\"The Army does not retreat. The Army does not negotiate. "
                "The Army arrives, and the Army prevails.\"*\n"
                "> — General Kovacs, High Command"
            ),
            inline=False,
        )
        embed.set_footer(text=f"Use /join army to enlist  •  COMMAND PROTOCOL")
        await interaction.response.send_message(embed=embed)

    # ── /rebels (lore) ────────────────────────────────────────────────────────

    @app_commands.command(name="rebels", description="View the Rebel Movement — lore, goals, and philosophy.")
    async def rebels_info(self, interaction: discord.Interaction):
        embed = rebels_embed(
            "THE REBEL MOVEMENT — FACTION DOSSIER",
            (
                "```\nCLASSIFICATION: INTERCEPTED TRANSMISSION\n"
                "FACTION CODE: OMEGA-FREE\nSTATUS: ACTIVE UNDERGROUND\n```\n\n"
                "**Overview**\n"
                "The Rebel Movement is not an army — it's an idea. Born from the brutal suppression "
                "of civilian populations, it grew into a decentralized network of fighters, hackers, "
                "engineers, and survivors. They have no central command, no uniform, and no mercy for "
                "oppressors. Every rebel chooses their own reason to fight.\n"
            ),
        )
        embed.add_field(
            name=f"{REBELS_ICON}  Philosophy",
            value=(
                "No kings. No commanders. No surrender.\n"
                "The Rebel Movement fights not to conquer, but to *liberate*."
            ),
            inline=False,
        )
        embed.add_field(
            name="⚡  Strengths",
            value=(
                "• Guerrilla ambush tactics\n"
                "• Stealth and infiltration units\n"
                "• Rapid hit-and-fade operations\n"
                "• Hacking and electronic warfare"
            ),
            inline=True,
        )
        embed.add_field(
            name="🔥  Strategic Goals",
            value=(
                "• Dismantle Army supply lines\n"
                "• Liberate occupied territories\n"
                "• Build a free people's network\n"
                "• Expose Army war crimes"
            ),
            inline=True,
        )
        embed.add_field(
            name="📻  Rebel Transmission",
            value=(
                "> *\"They built walls to keep us out. We learned to go under them, "
                "over them, and through them. The movement cannot be stopped — "
                "because the movement is everywhere.\"*\n"
                "> — Ghost, Rebel Command Cell 7"
            ),
            inline=False,
        )
        embed.set_footer(text=f"Use /join rebels to enlist  •  COMMAND PROTOCOL")
        await interaction.response.send_message(embed=embed)

    # ── /switchside ───────────────────────────────────────────────────────────

    @app_commands.command(name="switchside", description="Defect to the opposing faction (requires confirmation).")
    async def switchside(self, interaction: discord.Interaction):
        member = interaction.user
        guild = interaction.guild

        army_role = self._get_role(guild, "ARMY_ROLE_ID")
        rebels_role = self._get_role(guild, "REBELS_ROLE_ID")

        current_faction = None
        target_faction = None

        if army_role and army_role in member.roles:
            current_faction = "army"
            target_faction = "rebels"
        elif rebels_role and rebels_role in member.roles:
            current_faction = "rebels"
            target_faction = "army"

        if not current_faction:
            embed = warning_embed(
                "NO FACTION DETECTED",
                "You are not enlisted in any faction.\nUse `/join army` or `/join rebels` to enlist first.",
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Confirmation view
        view = SwitchConfirmView(self, interaction, target_faction)

        current_name = "The Army" if current_faction == "army" else "The Rebel Movement"
        target_name = "The Rebel Movement" if target_faction == "rebels" else "The Army"
        color = Colors.REBELS if target_faction == "rebels" else Colors.ARMY

        embed = base_embed(
            "⚠️  DEFECTION REQUEST",
            (
                f"```\nWARNING: FACTION LOYALTY CHANGE\n```\n"
                f"You are about to defect from **{current_name}** and join **{target_name}**.\n\n"
                f"This action will:\n"
                f"• Remove your current faction role\n"
                f"• Assign you to the opposing faction\n\n"
                f"Are you sure, soldier? **Confirm or stand down.**"
            ),
            color=color,
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ─── Switch Confirmation View ───────────────────────────────────────────────────

class SwitchConfirmView(discord.ui.View):
    def __init__(self, cog: FactionCog, original_interaction: discord.Interaction, target: str):
        super().__init__(timeout=30)
        self.cog = cog
        self.original_interaction = original_interaction
        self.target = target

    @discord.ui.button(label="CONFIRM DEFECTION", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()

        await interaction.response.edit_message(
            embed=success_embed(
                "PROCESSING DEFECTION",
                "Transferring faction allegiance..."
            ),
            view=None
        )

        await self.cog._assign_faction(interaction, self.target)

    @discord.ui.button(label="STAND DOWN", style=discord.ButtonStyle.secondary, emoji="🛑")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        embed = success_embed(
            "DEFECTION CANCELLED",
            "You have stood down. Your loyalty remains unchanged.",
        )
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        try:
            embed = warning_embed("REQUEST EXPIRED", "Defection request timed out. Stand down.")
            await self.original_interaction.edit_original_response(embed=embed, view=None)
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(FactionCog(bot))
