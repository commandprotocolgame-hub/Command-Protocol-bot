"""
Permission checks and helper decorators.
"""

import discord
from discord import app_commands
from functools import wraps
import logging

log = logging.getLogger("CommandProtocol.Checks")


def is_admin(config):
    """
    app_commands check: user must have a configured admin role OR server admin perms.
    Pass bot.config as the argument.
    """
    async def predicate(interaction: discord.Interaction) -> bool:
        # Server administrator always passes
        if interaction.user.guild_permissions.administrator:
            return True

        admin_role_ids = [int(rid) for rid in config.get_list("ADMIN_ROLE_IDS") if rid]
        if not admin_role_ids:
            # If no admin roles configured, fall back to administrator permission only
            return False

        user_role_ids = [role.id for role in interaction.user.roles]
        return any(rid in user_role_ids for rid in admin_role_ids)

    return app_commands.check(predicate)


async def send_permission_error(interaction: discord.Interaction):
    """Send a consistent permission denied embed."""
    from utils.embeds import error_embed
    embed = error_embed(
        "ACCESS DENIED",
        "```\nERROR 403: INSUFFICIENT CLEARANCE\n"
        "This operation requires ADMIN authorization.\n"
        "Stand down, soldier.\n```",
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
