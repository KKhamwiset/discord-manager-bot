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

# Config via env vars. Keep the live heartbeat thread as a safe default so a
# missing Railway env var does not silently disable the monitor.
DEFAULT_HEARTBEAT_CHANNEL_ID = 1514163672857972757


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        logger.warning("Invalid %s=%r; using %s", name, os.getenv(name), default)
        return default


HEARTBEAT_CHANNEL_ID = _env_int("HEARTBEAT_CHANNEL_ID", DEFAULT_HEARTBEAT_CHANNEL_ID)
HEARTBEAT_INTERVAL = _env_int("HEARTBEAT_INTERVAL", 120)  # cron sends every 2 min
# Give cron/Discord/API jitter room. The old 180s threshold was too close to
# the observed ~3 minute LLM-driven cron cadence and caused flaky presence.
HEARTBEAT_TIMEOUT = _env_int("HEARTBEAT_TIMEOUT", 360)
HEARTBEAT_EMOJI = os.getenv("HEARTBEAT_EMOJI", "💓")

# Status messages
STATUS_ONLINE = Game(name="In Sakura Garden 🌸")
STATUS_SLEEPING = Game(name="Mochi is sleeping~ 💤")

# Match the initial status from main.py — read INSTANCE env at import time.
# Treat common production spellings as online; keep local/dev idle.
_INSTANCE = os.getenv("INSTANCE", "Dev").strip().lower()
_INITIAL_STATUS = discord.Status.idle if _INSTANCE in {"dev", "devs", "development", "local"} else discord.Status.online


def _is_heartbeat_message(message) -> bool:
    """Return True for Hermes heartbeat pings in the configured channel."""
    if not HEARTBEAT_CHANNEL_ID or message.channel.id != HEARTBEAT_CHANNEL_ID:
        return False
    content = message.content or ""
    if HEARTBEAT_EMOJI not in content:
        return False
    return bool(message.author.bot or getattr(message, "webhook_id", None) or "Hermes heartbeat" in content)


class HeartbeatMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_heartbeat = None
        self.is_hermes_alive = False  # Start as False — let the first heartbeat or history fetch set it
        self.monitor.start()

    def cog_unload(self):
        self.monitor.cancel()

    @tasks.loop(seconds=120)  # check every 2 minutes to match cron interval
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

        if elapsed > HEARTBEAT_TIMEOUT:
            # Hermes is offline/stale. Always enforce sleeping presence, even if
            # our in-memory flag already says offline — the Discord presence may
            # have been reset by reconnect/startup or another cog.
            was_alive = self.is_hermes_alive
            self.is_hermes_alive = False
            try:
                await self.bot.change_presence(activity=STATUS_SLEEPING, status=Status.idle)
                if was_alive:
                    logger.info(f"💤 Hermes offline ({elapsed:.0f}s). sleeping~ 💤")
                else:
                    logger.debug(f"💤 Hermes still offline ({elapsed:.0f}s). Re-applied sleeping presence.")
            except Exception as e:
                logger.debug(f"change_presence failed: {e}")
        elif not self.is_hermes_alive:
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
                    else:
                        # Latest heartbeat exists but is stale — Hermes is offline.
                        # Enforce sleeping immediately instead of waiting for the
                        # next monitor tick; otherwise startup can leave the bot
                        # showing the default online presence forever.
                        self.is_hermes_alive = False
                        await self.bot.change_presence(activity=STATUS_SLEEPING, status=Status.idle)
                        logger.info(f"💤 Latest heartbeat is stale ({elapsed:.0f}s). Status → Mochi is sleeping~ 💤")
                    break
            else:
                # No heartbeat found in history — Hermes is likely offline
                # Keep last_heartbeat as None so the monitor loop will retry on next iteration
                self.is_hermes_alive = False
                await self.bot.change_presence(activity=STATUS_SLEEPING, status=Status.idle)
                logger.info(f"⚠️ No heartbeat found in history. Hermes may be offline — Status → Mochi is sleeping~ 💤")
        except Exception as e:
            logger.debug(f"Could not fetch heartbeat history: {e}")

    async def handle_heartbeat_message(self, message) -> bool:
        """Handle a heartbeat ping. Returns True when the message was consumed."""
        if not _is_heartbeat_message(message):
            return False

        self.last_heartbeat = message.created_at
        logger.debug(f"💓 Heartbeat received at {self.last_heartbeat}")

        if not self.is_hermes_alive:
            self.is_hermes_alive = True
            await self.bot.change_presence(activity=STATUS_ONLINE, status=_INITIAL_STATUS)
            logger.info(f"✅ Hermes heartbeat received! Status → In Sakura Garden 🌸 ({_INITIAL_STATUS})")
        return True

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for heartbeat messages in the designated channel."""
        await self.handle_heartbeat_message(message)

    @commands.Cog.listener()
    async def on_ready(self):
        """Re-apply presence on every gateway reconnect — discord.py restores status but drops activity."""
        if self.is_hermes_alive:
            await self.bot.change_presence(activity=STATUS_ONLINE, status=_INITIAL_STATUS)
            logger.info("🔄 Reconnected — restored Sakura Garden 🌸")
        else:
            await self.bot.change_presence(activity=STATUS_SLEEPING, status=Status.idle)
            logger.info("🔄 Reconnected — Hermes still offline, staying sleeping~ 💤")

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
