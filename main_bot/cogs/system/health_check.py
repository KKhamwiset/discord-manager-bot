"""
Health Check Cog for Mochi Bot
Periodically pings the Hermes gateway health endpoint and updates bot status.
"""
import os
import asyncio
import logging
import aiohttp
from discord.ext import commands, tasks
from discord import Game, Status

logger = logging.getLogger(__name__)

# Hermes gateway health check URL (set via env var)
HEALTH_URL = os.getenv("HEALTH_URL", "http://localhost:8000/health")
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))  # default 5 min

# Status messages
STATUS_ONLINE = Game(name="In Sakura Garden 🌸")
STATUS_SLEEPING = Game(name="Mochi is sleeping~ 💤")


class HealthCheck(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.is_hermes_alive = True
        self.health_check.start()

    def cog_unload(self):
        self.health_check.cancel()

    @tasks.loop(seconds=HEALTH_CHECK_INTERVAL)
    async def health_check(self):
        """Ping Hermes gateway and update status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(HEALTH_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    hermes_alive = resp.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
            hermes_alive = False

        if hermes_alive and not self.is_hermes_alive:
            self.is_hermes_alive = True
            await self.bot.change_presence(activity=STATUS_ONLINE, status=Status.online)
            logger.info("✅ Hermes is back online! Status → In Sakura Garden 🌸")
        elif not hermes_alive and self.is_hermes_alive:
            self.is_hermes_alive = False
            await self.bot.change_presence(activity=STATUS_SLEEPING, status=Status.idle)
            logger.info("💤 Hermes is offline. Status → Mochi is sleeping~ 💤")

    @health_check.before_loop
    async def before_health_check(self):
        await self.bot.wait_until_ready()
        logger.info(f"🔍 Health check started (interval: {HEALTH_CHECK_INTERVAL}s, target: {HEALTH_URL})")


async def setup(bot: commands.Bot):
    await bot.add_cog(HealthCheck(bot))
