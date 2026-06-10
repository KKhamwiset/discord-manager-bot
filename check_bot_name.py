import discord
import os
from dotenv import load_dotenv

# activate env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "main_bot", ".env"))

from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    user = bot.user
    print(f"✅ Bot name       : {user.name}")
    print(f"✅ Display name   : {user.display_name}")
    print(f"✅ Global name    : {getattr(user, 'global_name', 'N/A')}")
    print(f"✅ Bot ID         : {user.id}")
    print(f"✅ Avatar URL     : {user.avatar.url if user.avatar else 'N/A'}")
    await bot.close()

bot.run(os.getenv("DISCORD_TOKEN"))
