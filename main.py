import os, glob, logging, random, discord
import validation
from discord.ext import commands
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from web_server import keep_alive
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "discord_bot_db")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

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

    @commands.hybrid_command(help="Check bot latency")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.command(help="Say hello to the bot")
    async def hello(self, ctx: commands.Context):
        await ctx.send(f"Hello! {ctx.author.name}")

    @commands.hybrid_command(name="xdd", aliases=["xdx"], help="Random XD")
    async def greet(self, ctx: commands.Context):
        responses = [
            "XD",
            "xD",
            "Xd",
            "😂",
            "🤣",
            "Hahaha!",
            "That's funny!",
            "LMAO!",
            "ROFL!",
            "nga",
            "nigha",
            "<:xdx:1438479283147243572>",
            "<:xdd:1438479267716534353>",
        ]
        await ctx.send(random.choice(responses))

    @commands.hybrid_command(name="rick", aliases=["ing"], help="Generate random Ting emoji")
    async def generateEmoji(self, ctx: commands.Context, amount="1"):
        faces = ["<:ting2:1433595520424742983>", "<:ting:1433593486883684393>"]
        try:
            amount = int(amount)
        except:
            await ctx.send("❌ Please provide a valid number format.")
            return
        if amount > 10 or amount <= 0:
            await ctx.send("❌ Number out of range (1–10). Showing 10.")
            amount = 10
        await ctx.send("".join(random.choice(faces) for _ in range(amount)))


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

        self.is_paused = False
        self.mongo = Mongo(MONGO_URI, MONGO_DB)
        self.db = self.mongo.db
        self.add_check(validation.channel)
        self.add_check(self.check_maintenance_mode)

        print("✅ Mongo connected" if self.db is not None else "❌ Mongo failed")

    async def check_maintenance_mode(self, ctx):
        if not self.is_paused:
            return True
        if ctx.command.name == "resume":
            return True
        return False

    async def refactor_db(self,enabled=False):
        if not enabled:
            return
        
        print("🔄 Starting Migration...")
        db = self.db["schedules"]
        cursor = db.find({})
        data = await cursor.to_list(length=None)
        schema = {}
        for i in data:
            user_id = i.get("user_id")
            day =  i.get("day_en","").strip()

            if user_id not in schema:
                schema[user_id] = {"user_id" : user_id}

            if day not in schema[user_id]:
                schema[user_id][day] = []
            new_data = {
                "name" : i.get("subject"),
                "room" : i.get("room","Unknown"),
                "time" : i.get("time"),
                "professor" : "Unknown"
            }
            schema[user_id][day] += [new_data]

        new_data = list(schema.values())
        if new_data:
            await db.delete_many({})
            await db.insert_many(new_data)
        else:
            print("❌ Error: Transformation resulted in empty list. Aborting wipe.")
        print("✅ Done Migrations")
        
            
    async def setup_hook(self):
        print("Starting Setup Hook...")
        await self.mongo.pingdb()
        await self.add_cog(Core(self))
        await self._load_all_extensions() 

        if os.getenv("ENV") == "SINGLE_GUILD":
            target_guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=target_guild)
            await self.tree.sync(guild=target_guild)
            
        else:
            print("🌍 Production Mode: Syncing Globally...")
            await self.tree.sync()
        await self.refactor_db()

    async def on_ready(self):
        guild = self.get_guild(GUILD_ID)
        if guild:
            print(f"✅ Connected to guild: {guild.name} (ID: {guild.id})")
        else:
            print("⚠️ Guild not found in cache. Are you sure GUILD_ID is correct?")
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
log_level_shift = logging.ERROR if bool(os.getenv("DEV")) == True else logging.DEBUG
Bot.run(TOKEN, log_handler=handler, log_level=log_level_shift)
