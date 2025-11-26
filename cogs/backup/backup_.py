import discord
from discord.ext import commands
import asyncio 
import zipfile
import os
import datetime
import motor.motor_asyncio 
import validation

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MAIN_DB")

    @commands.hybrid_command(name="backup", help="Backup the database (Async).")
    @validation.role()
    async def backup(self, ctx):
        backup_channel_id = os.getenv("BACKUP_CHANNEL_ID")
        if not backup_channel_id:
             await ctx.send("❌ BACKUP_CHANNEL_ID is not set.")
             return

        channel = self.bot.get_channel(int(backup_channel_id))
        if not channel:
            await ctx.send("❌ Channel not found.")
            return

        await ctx.send("⏳ Starting Async Backup... (Bot will remain responsive)")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_filename = f"db_backup_{timestamp}.zip"
        generated_files = [] 

        try:

            collections = await self.db.list_collection_names()

            if not collections:
                await ctx.send("❌ No collections found.")
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
                limit = ctx.guild.filesize_limit if ctx.guild else 8 * 1024 * 1024

                if file_size > (limit / (1024*1024)):
                    await channel.send(f"⚠️ Backup too large ({file_size:.2f}MB).")
                else:
                    file = discord.File(zip_filename)
                    await channel.send(
                        f"📦 **Async Backup** for `{self.db_name}`\nCollections: {len(generated_files)}", 
                        file=file
                    )
                    await ctx.send("✅ Done!")
            else:
                await ctx.send("❌ Zip file creation failed.")

        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
            print(f"Backup Error: {e}")

        finally:
            # Cleanup
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
            for f in generated_files:
                if os.path.exists(f):
                    os.remove(f)

async def setup(bot):
    await bot.add_cog(Backup(bot))