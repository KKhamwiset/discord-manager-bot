import discord
from discord.ext import commands, tasks
import asyncio 
import zipfile
import os
import datetime
import logging

logger = logging.getLogger(__name__)

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MAIN_DB")

    async def cog_load(self):
        if self.bot.instance == "server":
            self.backup_task.start()
        else:
            self.backup_task.cancel()

    async def cog_unload(self):
        self.backup_task.cancel()

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=7))))
    async def backup_task(self):
        await self.run_backup()

    async def run_backup(self, ctx=None):
        backup_channel_id = os.getenv("BACKUP_CHANNEL_ID")
        if not backup_channel_id:
             msg = "❌ BACKUP_CHANNEL_ID is not set."
             logger.error(msg)
             if ctx: await ctx.send(msg)
             return

        channel = self.bot.get_channel(int(backup_channel_id))
        if not channel:
            msg = "❌ Backup channel not found."
            logger.error(msg)
            if ctx: await ctx.send(msg)
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_filename = f"db_backup_{timestamp}.zip"
        generated_files = [] 

        if ctx: await ctx.send(f"⏳ Starting backup for `{self.db_name}`...")
        logger.info(f"Starting backup for {self.db_name}")

        try:
            collections = await self.db.list_collection_names()

            if not collections:
                msg = "❌ No collections found."
                logger.warning(msg)
                if ctx: await ctx.send(msg)
                return
            
            for col in collections:
                json_filename = f"{col}.json"
                
                command = (
                    f'mongoexport --uri="{self.mongo_uri}" '
                    f'--db={self.db_name} --collection={col} '
                    f'--out={json_filename} --jsonArray --pretty '
                    f'--jsonFormat=canonical'
                )
                
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    err_msg = f"Failed to export {col}: {stderr.decode()}"
                    logger.error(err_msg)
                    if ctx: await ctx.send(f"⚠️ {err_msg}")
                    continue
                
                generated_files.append(json_filename)

            if not generated_files:
                logger.warning("No files were exported during backup.")
                if ctx: await ctx.send("❌ No files were exported.")
                return

            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f in generated_files:
                    if os.path.exists(f):
                        zipf.write(f)

            if os.path.exists(zip_filename):
                file_size = os.path.getsize(zip_filename) / (1024 * 1024)
                limit = channel.guild.filesize_limit if channel.guild else 8 * 1024 * 1024

                if file_size > (limit / (1024*1024)):
                    await channel.send(f"⚠️ Backup too large ({file_size:.2f}MB).")
                    if ctx: await ctx.send(f"⚠️ Backup too large ({file_size:.2f}MB).")
                    logger.warning(f"Backup too large ({file_size:.2f}MB)")
                else:
                    file = discord.File(zip_filename)
                    await channel.send(
                        f"**Backup** for `{self.db_name}`\nCollections: {len(generated_files)}", 
                        file=file
                    )
                    if ctx: await ctx.send(f"✅ Backup completed and sent to <#{backup_channel_id}>.")
                    logger.info("Backup completed successfully and sent to Discord.")
            else:
                msg = "❌ Zip file creation failed."
                logger.error(msg)
                if ctx: await ctx.send(msg)

        except Exception as e:
            err_msg = f"❌ Backup Error: {e}"
            await channel.send(err_msg)
            logger.exception("Backup Error")
            if ctx: await ctx.send(err_msg)

        finally:
            # Cleanup
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
            for f in generated_files:
                if os.path.exists(f):
                    os.remove(f)

    @commands.command(name="backup", help="Manually trigger a database backup")
    @commands.is_owner()
    async def manual_backup(self, ctx):
        await self.run_backup(ctx)

    @backup_task.before_loop
    async def before_backup_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Backup(bot))