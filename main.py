import os, glob, logging, random, discord
from discord.ext import commands
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from web_server import keep_alive
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "discord_bot_db")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


TARGET_PREFIXES = ["b", "t"]

async def get_case_insensitive_prefix(bot, message: discord.Message):
    prefixes = []
    prefixes += [*commands.when_mentioned(bot, message)]

    for p in TARGET_PREFIXES:
        prefixes += [p, p.upper()]

    return prefixes

class Mongo:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000, maxPoolSize=20)
        self.db = self.client[db_name]

    async def pingdb(self):
        await self.client.admin.command("ping")

    async def close(self):
        self.client.close()


class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f"Hello! {ctx.author.name}")

    @commands.command(name="xdd", aliases=["xdx"])
    async def greet(self, ctx: commands.Context):
        responses = ["XD", "xD", "Xd", "😂", "🤣", "Hahaha!", "That's funny!", "LMAO!", "ROFL!","nga","nigha"]
        await ctx.send(random.choice(responses))

    @commands.command(name="rick", aliases=["ing"])
    async def generateEmoji(self, ctx: commands.Context, n: int = 1):
        faces = ["<:ting2:1433595520424742983>", "<:ting:1433593486883684393>"]
        if n > 10 or n <= 0:
            await ctx.send("❌ Number out of range (1–10). Showing 10.")
            n = 10
        await ctx.send("".join(random.choice(faces) for _ in range(n)))


class BotInitDB(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_case_insensitive_prefix,
            case_insensitive=True,
            intents=intents,
            help_command=None,
        )
        if not TOKEN or not MONGO_URI:
            raise RuntimeError("Missing TOKEN or MONGO_URI")
        self.mongo = Mongo(MONGO_URI, MONGO_DB)
        self.db = self.mongo.db
        print("✅ Mongo connected" if self.db is not None else "❌ Mongo failed")

    async def setup_hook(self):
        await self.mongo.pingdb()
        await self.add_cog(Core(self))
        await self._load_all_extensions()

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")

    async def close(self):
        await self.mongo.close()
        await super().close()

    async def _load_all_extensions(self, exclude: list[str] | None = None):
        exclude = exclude or []
        paths = glob.glob("cogs/**/*.py", recursive=True)
        for path in paths:
            base = os.path.basename(path)
            if base.startswith("_") or any(i in exclude for i in base.split(".")):
                continue
            mod = path[:-3].replace(os.sep, ".")
            await self.load_extension(mod)



# ------------ run -----------
keep_alive()
Bot = BotInitDB()
Bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
