import discord
from discord.ext import commands
import logging
import os
import subprocess
import validation

class Maintenance(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    @commands.hybrid_command(name="pause", help="Pauses the bot (Maintenance Mode).")
    @validation.manage_guild()
    async def pause_bot(self, ctx, instance: str = None):
        if instance is not None and instance not in ["server","dev"]:
            await ctx.send("⚠️ Invalid instance.")
            return
        if not instance:
            instance = self.bot.instance
        if self.bot.is_paused and (self.bot.instance == instance):
            await ctx.send("⚠️ Bot is already paused.")
            return
        if (self.bot.instance == instance):
            await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Maintenance Mode"))
            await ctx.send(f"⏸️ {instance.title()} bot paused.")
            self.bot.is_paused = True
            logging.info(f"Bot paused by {ctx.author}")

    @commands.hybrid_command(name="resume", help="Resumes the bot from Maintenance Mode.")
    @validation.manage_guild()
    async def resume_bot(self, ctx, instance: str = None):
        if instance is not None and instance not in ["server","dev"]:
            await ctx.send("⚠️ Invalid instance.")
            return
        if not instance:
            instance = self.bot.instance
        if not self.bot.is_paused and (self.bot.instance == instance):
            await ctx.send("⚠️ Bot is not paused.")
            return
        if (self.bot.instance == instance):
            self.bot.is_paused = False
            await self.bot.change_presence(status=discord.Status.online,activity=discord.Game("Nguyen~" if self.bot.instance == "server" else "Dev~"))    
            await ctx.send(f"▶️ {instance.title()} bot resumed. Back online!")
            logging.info(f"Bot resumed by {ctx.author}")



    @commands.hybrid_command(name="restart", help="Restart the Hermes gateway (Windows external restart)")
    @validation.owner_only()
    async def restart_gateway(self, ctx, instance: str = None):
        """Restart Hermes gateway by calling CLI externally.
        
        On Windows with Scheduled Tasks, internal restart is blocked to prevent restart loops.
        This command spawns a detached subprocess to run 'hermes gateway restart' externally.
        """
        if instance is not None and instance not in ["server", "dev"]:
            await ctx.send("⚠️ Invalid instance.")
            return
        if not instance:
            instance = self.bot.instance
        
        # Only proceed if the instance matches
        if self.bot.instance != instance:
            await ctx.send(f"⚠️ This bot instance is '{self.bot.instance}', not '{instance}'.")
            return

        await ctx.send(f"🔄 Restarting Hermes gateway ({instance})... This may take 30-60 seconds.")
        
        try:
            # Use subprocess to run hermes gateway restart externally
            # This bypasses the internal safety guard
            env = os.environ.copy()
            env["HERMES_HOME"] = env.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
            
            # Run hermes gateway restart in background
            process = subprocess.Popen(
                ["hermes", "gateway", "restart"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            
            # Don't wait for completion - let it run detached
            # The gateway will shut down and systemd/scheduled task will restart it
            
            logging.info(f"Gateway restart requested by {ctx.author} for instance {instance}")
            
        except FileNotFoundError:
            await ctx.send("❌ `hermes` command not found in PATH. Is Hermes installed?")
            logging.error("hermes command not found for restart")
        except Exception as e:
            await ctx.send(f"❌ Failed to initiate restart: {e}")
            logging.error(f"Restart failed: {e}")

async def setup(bot):
    await bot.add_cog(Maintenance(bot))
