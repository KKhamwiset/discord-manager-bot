"""
Heartbeat Monitor Cog for Mochi Bot
Monitors Hermes heartbeat messages in a designated Discord channel.
Changes bot status based on whether Hermes is alive.
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks
from discord import Game, Status

logger = logging.getLogger(__name__)

# Config via env vars
HEARTBEAT_CHANNEL_ID = int(os.getenv("HEARTBEAT_CHANNEL_ID", "0"))
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "300"))  # 5 min default
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", "600"))    # 10 min default
HEARTBEAT_EMOJI = os.getenv("HEARTBEAT_EMOJI", "💓")

# Status messages
STATUS_ONLINE = Game(name="In Sakura Garden 🌸")
STATUS_SLEEPING = Game(name="Mochi is sleeping~ 💤")


class HeartbeatMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_heartbeat = None
        self.is_hermes_alive = True
        self.monitor.start()

    def cog_unload(self):
        self.monitor.cancel()

    @tasks.loop(seconds=60)  # check every minute
    async def monitor(self):
        """Check if heartbeat is still fresh."""
        if not HEARTBEAT_CHANNEL_ID:
            return

        now = datetime.now(tz=timezone.utc)

        if self.last_heartbeat is None:
            # Haven't received any heartbeat yet, try to find the latest one
            await self._fetch_latest_heartbeat()
            return

        elapsed = (now - self.last_heartbeat).total_seconds()

        if elapsed > HEARTBEAT_TIMEOUT and self.is_hermes_alive:
            # Hermes went offline
            self.is_hermes_alive = False
            await self.bot.change_presence(activity=STATUS_SLEEPING, status=Status.idle)
            logger.info(f"💤 Hermes heartbeat timeout ({elapsed:.0f}s). Status → Mochi is sleeping~ 💤")
        elif elapsed <= HEARTBEAT_TIMEOUT and not self.is_hermes_alive:
            # Hermes came back
            self.is_hermes_alive = True
            await self.bot.change_presence(activity=STATUS_ONLINE, status=Status.online)
            logger.info("✅ Hermes heartbeat restored! Status → In Sakura Garden 🌸")

    async def _fetch_latest_heartbeat(self):
        """Fetch the latest heartbeat message from the channel."""
        channel = self.bot.get_channel(HEARTBEAT_CHANNEL_ID)
        if not channel:
            return

        try:
            # Look for recent heartbeat messages (from the bot itself or a webhook)
            async for msg in channel.history(limit=20):
                if msg.author == self.bot.user and HEARTBEAT_EMOJI in msg.content:
                    self.last_heartbeat = msg.created_at
                    break
        except Exception as e:
            logger.debug(f"Could not fetch heartbeat history: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for heartbeat messages in the designated channel."""
        if not HEARTBEAT_CHANNEL_ID:
            return
        if message.channel.id != HEARTBEAT_CHANNEL_ID:
            return
        if HEARTBEAT_EMOJI in message.content:
            self.last_heartbeat = message.created_at
            logger.debug(f"💓 Heartbeat received at {self.last_heartbeat}")

            if not self.is_hermes_alive:
                self.is_hermes_alive = True
                await self.bot.change_presence(activity=STATUS_ONLINE, status=Status.online)
                logger.info("✅ Hermes heartbeat received! Status → In Sakura Garden 🌸")

    @monitor.before_loop
    async def before_monitor(self):
        await self.bot.wait_until_ready()
        if HEARTBEAT_CHANNEL_ID:
            logger.info(f"💓 Heartbeat monitor started (channel: {HEARTBEAT_CHANNEL_ID}, timeout: {HEARTBEAT_TIMEOUT}s)")
        else:
            logger.warning("⚠️ HEARTBEAT_CHANNEL_ID not set, heartbeat monitor disabled")


async def setup(bot: commands.Bot):
    await bot.add_cog(HeartbeatMonitor(bot))
