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
    command_prefix=commands.when_mentioned_or("b","t"),
    case_insensitive=True,
    intents=intents,
    help_command=None
)

async def _load_all_extensions(exclude: list[str] = []):
    paths = glob.glob("cogs/*.py") + glob.glob("cogs/**/*.py", recursive=True)
    for path in paths:
        if os.path.basename(path).startswith("_") or any(i in exclude for i in os.path.basename(path).split('.')):

            continue
        mod = path[:-3].replace(os.sep, ".")  
        await bot.load_extension(mod)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def setup_hook():
    await _load_all_extensions([]) 

@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send(f"Hello! {ctx.author.name}")

@bot.command(name="xdd",aliases=["xdx"])
async def greet(ctx: commands.Context):
    await ctx.send(f"xdd {ctx.author.name}")


@bot.command(name="rick",aliases=["ing"])
async def generateEmoji(ctx: commands.Context, n: int = 1):
    faces = ["<:ting2:1433595520424742983>", "<:ting:1433593486883684393>"]
    if n > 10 or n <= 0:
        await ctx.send("❌ Number of bricks out of range (1–10). Showing 10.")
        n = 10
    await ctx.send("".join(random.choice(faces) for _ in range(n)))

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
