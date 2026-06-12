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
import discord

logger = logging.getLogger(__name__)

# Config via env vars
HEARTBEAT_CHANNEL_ID = int(os.getenv("HEARTBEAT_CHANNEL_ID", "0"))
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "300"))  # 5 min default
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", "60"))     # 1 min default
HEARTBEAT_EMOJI = os.getenv("HEARTBEAT_EMOJI", "💓")

# Status messages
STATUS_ONLINE = Game(name="In Sakura Garden 🌸")
STATUS_SLEEPING = Game(name="Mochi is sleeping~ 💤")

# Match the initial status from main.py — read INSTANCE env at import time
_INSTANCE = os.getenv("INSTANCE", "Dev")
_INITIAL_STATUS = discord.Status.online if _INSTANCE == "Server" else discord.Status.idle


class HeartbeatMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_heartbeat = None
        self.is_hermes_alive = False  # Start as False — let the first heartbeat or history fetch set it
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
            try:
                await self.bot.change_presence(activity=STATUS_SLEEPING, status=Status.idle)
                logger.info(f"💤 Hermes offline ({elapsed:.0f}s). sleeping~ 💤")
            except Exception as e:
                logger.debug(f"change_presence failed: {e}")
        elif elapsed <= HEARTBEAT_TIMEOUT and not self.is_hermes_alive:
            # Hermes came back
            self.is_hermes_alive = True
            try:
                await self.bot.change_presence(activity=STATUS_ONLINE, status=_INITIAL_STATUS)
                logger.info(f"✅ Hermes restored! Sakura Garden ({_INITIAL_STATUS})")
            except Exception as e:
                logger.debug(f"change_presence failed: {e}")

    async def _fetch_latest_heartbeat(self):
        """Fetch the latest heartbeat message from the channel and restore status if fresh."""
        channel = self.bot.get_channel(HEARTBEAT_CHANNEL_ID)
        if not channel:
            return

        try:
            # Look for recent heartbeat messages (check emoji only — sender may be webhook)
            async for msg in channel.history(limit=20):
                if HEARTBEAT_EMOJI in msg.content:
                    self.last_heartbeat = msg.created_at
                    # Check if the heartbeat is still fresh
                    now = datetime.now(tz=timezone.utc)
                    elapsed = (now - self.last_heartbeat).total_seconds()
                    if elapsed <= HEARTBEAT_TIMEOUT:
                        # Heartbeat is fresh — restore online status
                        self.is_hermes_alive = True
                        await self.bot.change_presence(activity=STATUS_ONLINE, status=_INITIAL_STATUS)
                        logger.info(f"✅ Fresh heartbeat found in history. Status → In Sakura Garden 🌸 ({_INITIAL_STATUS})")
                    break
            else:
                # No heartbeat found in history — Hermes is likely offline
                self.last_heartbeat = datetime.now(tz=timezone.utc)
                self.is_hermes_alive = False
                await self.bot.change_presence(activity=STATUS_SLEEPING, status=Status.idle)
                logger.info(f"⚠️ No heartbeat found in history. Hermes may be offline — Status → Mochi is sleeping~ 💤")
        except Exception as e:
            logger.debug(f"Could not fetch heartbeat history: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for heartbeat messages in the designated channel."""
        if not HEARTBEAT_CHANNEL_ID:
            return
        if message.channel.id != HEARTBEAT_CHANNEL_ID:
            return
        # Accept messages from the bot itself (heartbeat sender) or webhooks
        # Check emoji content to confirm it's actually a heartbeat
        if message.author.bot and HEARTBEAT_EMOJI in message.content:
            self.last_heartbeat = message.created_at
            logger.debug(f"💓 Heartbeat received at {self.last_heartbeat}")

            if not self.is_hermes_alive:
                self.is_hermes_alive = True
                await self.bot.change_presence(activity=STATUS_ONLINE, status=_INITIAL_STATUS)
                logger.info(f"✅ Hermes heartbeat received! Status → In Sakura Garden 🌸 ({_INITIAL_STATUS})")

    @monitor.before_loop
    async def before_monitor(self):
        await self.bot.wait_until_ready()
        if HEARTBEAT_CHANNEL_ID:
            # Try to restore status from history on startup
            await self._fetch_latest_heartbeat()
            logger.info(f"💓 Heartbeat monitor started (channel: {HEARTBEAT_CHANNEL_ID}, timeout: {HEARTBEAT_TIMEOUT}s)")
        else:
            logger.warning("⚠️ HEARTBEAT_CHANNEL_ID not set, heartbeat monitor disabled")


async def setup(bot: commands.Bot):
    await bot.add_cog(HeartbeatMonitor(bot))
