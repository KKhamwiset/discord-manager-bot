import discord
from discord.ext import commands
import logging
import os
import validation

class Maintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.hybrid_command(name="pause", help="Pauses the bot (Maintenance Mode).")
    @validation.role()
    async def pause_bot(self, ctx, instance: str = None):
        if instance is not None and instance not in ["server","dev"]:
            await ctx.send("⚠️ Invalid instance.")
            return
        if not instance:
            instance = self.bot.instance
        if self.bot.is_paused:
            await ctx.send("⚠️ Bot is already paused.")
            return
        if (self.bot.instance == instance):
            await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Maintenance Mode"))
            await ctx.send(f"⏸️ {instance.title()} bot paused.")
            self.bot.is_paused = True
            logging.info(f"Bot paused by {ctx.author}")

    @commands.hybrid_command(name="resume", help="Resumes the bot from Maintenance Mode.")
    @validation.role()
    async def resume_bot(self, ctx, instance: str = None):
        if instance is not None and instance not in ["server","dev"]:
            await ctx.send("⚠️ Invalid instance.")
            return
        if not instance:
            instance = self.bot.instance
        if not self.bot.is_paused:
            await ctx.send("⚠️ Bot is not paused.")
            return
        if (self.bot.instance == instance):
            self.bot.is_paused = False
            await self.bot.change_presence(status=discord.Status.online,activity=discord.Game("Nguyen~" if self.bot.instance == "server" else "Dev~"))    
            await ctx.send(f"▶️ {instance.title()} bot resumed. Back online!")
            logging.info(f"Bot resumed by {ctx.author}")

async def setup(bot):
    await bot.add_cog(Maintenance(bot))
