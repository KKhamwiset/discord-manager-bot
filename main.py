import os, logging, random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import glob

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is not set")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('b'),
    intents=intents,
    help_command=None
)

async def _load_all_extensions():
    paths = glob.glob("cogs/*.py") + glob.glob("cogs/**/*.py", recursive=True)
    for path in paths:
        if os.path.basename(path).startswith("_"):
            continue
        mod = path[:-3].replace(os.sep, ".")  
        await bot.load_extension(mod)

@bot.event
async def on_ready():
    await _load_all_extensions()
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send(f"Hello! {ctx.author.name}")

@bot.command()
async def xdd(ctx: commands.Context):
    await ctx.send(f"xdd {ctx.author.name}")

@bot.command()
async def info(ctx: commands.Context):
    embed = discord.Embed(
        title="Bot Info",
        description="This is a simple info command using embeds!",
        color=discord.Color.blue()
    )
    if ctx.author.avatar:
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    if ctx.bot.user and ctx.bot.user.avatar:
        embed.set_thumbnail(url=ctx.bot.user.avatar.url)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)} ms", inline=False)
    embed.add_field(name="Server", value=ctx.guild.name if ctx.guild else "DM", inline=False)
    embed.set_footer(text=f"Requested by {ctx.author.name}")

    await ctx.send(embed=embed)

@bot.command(name="brick")  # rename to match your help text
async def brick(ctx: commands.Context, n: int = 1):
    faces = ["<:ting2:1433595520424742983>", "<:ting:1433593486883684393>"]
    if n > 10 or n <= 0:
        await ctx.send("❌ Number of bricks out of range (1–10). Showing 10.")
        n = 10
    await ctx.send("".join(random.choice(faces) for _ in range(n)))

@bot.command()
async def help(ctx: commands.Context):
    embed = discord.Embed(
        title="🤖 Bot Help Menu",
        description="Here are all available commands!",
        color=discord.Color.blurple()
    )
    if ctx.author.avatar:
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    if ctx.bot.user and ctx.bot.user.avatar:
        embed.set_thumbnail(url=ctx.bot.user.avatar.url)

    embed.add_field(
        name="🧩 General",
        value=(
            "`bping` → Check bot latency\n"
            "`bhello` → Say hello to the bot\n"
            "`binfo` → Show bot/server info\n"
            "`bbrick [n]` → Send random brick emojis (1–10)"
        ),
        inline=False
    )
    embed.add_field(
        name="🛠️ Role Management",
        value=(
            "`bcrole <role_name> [#color]` → Create a new role (random color if none)\n"
            "`brrole <role_name>` → Remove a role by name\n"
            "`barole <role_name> @user1 @user2 ...` → Add role to mentioned users"
        ),
        inline=False
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
