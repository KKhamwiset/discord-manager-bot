import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=intents, help_command=None)

def role_validate(roles):
    if not any("Moderator" in i.name for i in roles):
        return False
    return True

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello! {ctx.author.name}")

@bot.command()
async def help(cmd):
    await cmd.send(f"Help! {cmd.author.name}")

@bot.command()
async def xdd(cmd):
    await cmd.send(f"xdd {cmd.author.name}")

@bot.command()
async def crole(ctx, role_name: str, color: str = None):
    guild = ctx.guild
    existing_role = discord.utils.get(guild.roles, name=role_name)

    if existing_role:
        await ctx.send(f"⚠️ Role `{existing_role.name}` already exists.")
        return

    # 🎨 choose color
    if color:
        # try to convert hex -> int
        try:
            color_value = discord.Color(int(color.lstrip('#'), 16))
        except ValueError:
            await ctx.send("❌ Invalid color format! Use a hex code like `#FF0000`.")
            return
    else:
        # no color provided → random color
        color_value = discord.Color.random()

    # create the role
    new_role = await guild.create_role(name=role_name, color=color_value)
    await ctx.send(f"✅ Created role `{new_role.name}` with color `{color_value}`")
    
@bot.command()
async def rrole(ctx, role_name: str):
    guild = ctx.guild
    existing_role = discord.utils.get(guild.roles, name=role_name)

    if not existing_role:
        await ctx.send(f"⚠️ Role `{role_name}` does not exist.")
        return

    await existing_role.delete()
    await ctx.send(f"✅ Deleted role `{role_name}`")

@bot.command()
async def arole(ctx, role_name: str):
    validate = role_validate(ctx.author.roles)
    if not validate:
        await ctx.send("❌ You need to be a bot admin to use this command.")
        return
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=role_name)

    if not role:
        await ctx.send(f"⚠️ Role `{role_name}` does not exist.")
        return

    # Get all mentioned users in the command message
    mentioned_members = ctx.message.mentions

    if not mentioned_members:
        await ctx.send("❌ You need to mention at least one user.")
        return

    # Add the role to each mentioned user
    for member in mentioned_members:
        await member.add_roles(role)
        await ctx.send(f"✅ Added role `{role.name}` to {member.mention}")

    await ctx.send(f"🎉 Done! Role `{role.name}` added to all mentioned users.")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)