import discord
from discord.ext import commands
import logging
import os
import validation

class Maintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.instance = "Server" if bool(os.getenv("DEV")) else "Dev" + " instance"
    @commands.hybrid_command(name="pause", help="Pauses the bot (Maintenance Mode).")
    @validation.role()
    async def pause_bot(self, ctx):
        if self.bot.is_paused:
            await ctx.send("⚠️ Bot is already paused.")
            return
        
        self.bot.is_paused = True
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Maintenance Mode"))
        await ctx.send(f"⏸️ {instance} bot paused. Entering Maintenance Mode.")
        logging.info(f"Bot paused by {ctx.author}")

    @commands.hybrid_command(name="resume", help="Resumes the bot from Maintenance Mode.")
    @validation.role()
    async def resume_bot(self, ctx):
        if not self.bot.is_paused:
            await ctx.send("⚠️ Bot is not paused.")
            return

        self.bot.is_paused = False
        await self.bot.change_presence(status=discord.Status.online)
        await ctx.send(f"▶️ {instance} bot resumed. Back online!")
        logging.info(f"Bot resumed by {ctx.author}")

async def setup(bot):
    await bot.add_cog(Maintenance(bot))
