import discord
from discord.ext import commands


class ChannelConfiguration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.collection = self.bot.db["homeworks"] 
            print("✅ Channel Cog connection, OK.")
        except Exception as e:
            print(f"❌ Channel Cog connection failed: {e}")
            self.collection = None
async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelConfiguration(bot))