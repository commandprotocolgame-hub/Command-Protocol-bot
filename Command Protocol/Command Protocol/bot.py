"""
Command Protocol Discord Bot
Main entry point - initializes and runs the bot.
"""

import discord
from discord.ext import commands
import asyncio
import logging
import os
from pathlib import Path

from utils.config import Config
from utils.data_manager import DataManager

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("CommandProtocol")


# ─── Bot Setup ──────────────────────────────────────────────────────────────────
class CommandProtocolBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix="!",  # Fallback prefix (slash commands are primary)
            intents=intents,
            help_command=None,
        )

        self.config = Config()
        self.data_manager = DataManager()

    async def setup_hook(self):
        """Load all cogs and sync slash commands."""
        cogs = [
            "cogs.faction",
            "cogs.information",
            "cogs.community",
            "cogs.admin",
            "cogs.moderation",
            "cogs.welcome",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                log.info(f"Loaded cog: {cog}")
            except Exception as e:
                log.error(f"Failed to load cog {cog}: {e}")

        # Sync slash commands globally (use guild_id for instant sync during dev)
        guild_id = self.config.get("GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info(f"Slash commands synced to guild {guild_id}")
        else:
            await self.tree.sync()
            log.info("Slash commands synced globally")

    async def on_ready(self):
        log.info(f"╔══════════════════════════════════════╗")
        log.info(f"║   COMMAND PROTOCOL BOT — ONLINE      ║")
        log.info(f"║   Logged in as: {self.user}         ")
        log.info(f"║   ID: {self.user.id}               ")
        log.info(f"╚══════════════════════════════════════╝")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the battlefield | /about",
            )
        )

    async def on_command_error(self, ctx, error):
        log.error(f"Command error: {error}")


# ─── Run ────────────────────────────────────────────────────────────────────────
async def main():
    bot = CommandProtocolBot()
    token = bot.config.get("BOT_TOKEN")

    if not token or token == "YOUR_BOT_TOKEN_HERE":
        log.critical("No BOT_TOKEN set in config.json! Exiting.")
        return

    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())