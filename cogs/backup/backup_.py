import discord
from discord.ext import commands, tasks
import asyncio 
import zipfile
import os
import datetime

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

    @tasks.loop(time=datetime.time(hour=0, minute=0,tzinfo=datetime.timezone(datetime.timedelta(hours=7))))
    async def backup_task(self):
        backup_channel_id = os.getenv("BACKUP_CHANNEL_ID")
        if not backup_channel_id:
             print("❌ BACKUP_CHANNEL_ID is not set.")
             return

        channel = self.bot.get_channel(int(backup_channel_id))
        if not channel:
            print("❌ Backup channel not found.")
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_filename = f"db_backup_{timestamp}.zip"
        generated_files = [] 

        try:

            collections = await self.db.list_collection_names()

            if not collections:
                print("❌ No collections found.")
                return
            
            for col in collections:
                json_filename = f"{col}.json"
                
                command = (
                    f'mongoexport --uri="{self.mongo_uri}" '
                    f'--db={self.db_name} --collection={col} '
                    f'--out={json_filename} --jsonArray --pretty'
                )
                
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    print(f"Failed to export {col}: {stderr.decode()}")
                    continue
                
                generated_files.append(json_filename)

            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f in generated_files:
                    if os.path.exists(f):
                        zipf.write(f)

            if os.path.exists(zip_filename):
                file_size = os.path.getsize(zip_filename) / (1024 * 1024)
                limit = channel.guild.filesize_limit if channel.guild else 8 * 1024 * 1024

                if file_size > (limit / (1024*1024)):
                    await channel.send(f"⚠️ Backup too large ({file_size:.2f}MB).")
                else:
                    file = discord.File(zip_filename)
                    await channel.send(
                        f"📦 **Async Backup** for `{self.db_name}`\nCollections: {len(generated_files)}", 
                        file=file
                    )
            else:
                print("❌ Zip file creation failed.")

        except Exception as e:
            await channel.send(f"❌ Backup Error: {e}")
            print(f"Backup Error: {e}")

        finally:
            # Cleanup
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
            for f in generated_files:
                if os.path.exists(f):
                    os.remove(f)

    @backup_task.before_loop
    async def before_backup_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Backup(bot))