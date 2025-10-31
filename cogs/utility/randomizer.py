import os
import random
import asyncio
import discord
from discord.ext import commands
import pymongo


MONGO_URI = os.getenv("MONGO_URI")
DELAY_SEC = 0.6 


class Randomizer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        try:
            self.client = pymongo.MongoClient(MONGO_URI)
            self.db = self.client["discord_bot_db"]
            self.collection = self.db["restaurant_choices"]
            print("✅ MongoDB connection successful for Randomizer Cog.")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.client = None

    # ---------- util: embed + send ----------
    def role_validate(self, roles : list[discord.Role]):
        if not any("Moderator" in i.name for i in roles):
            return False
        return True

    async def send_embed(
        self,
        ctx: commands.Context,
        title: str,
        description: str,
        color: discord.Color = discord.Color.blurple(),
        footer: str | None = None,
    ):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_author(name=str(ctx.author), icon_url=getattr(ctx.author.display_avatar, "url", discord.Embed))
        if footer:
            embed.set_footer(text=footer)
        async with ctx.typing():
            await asyncio.sleep(DELAY_SEC)
            await ctx.send(embed=embed)

    # ---------- commands ----------
    @commands.command(name="arand", aliases=["asr", "assr"])
    async def add_rand(self, ctx: commands.Context,*args):
        
        """Add a restaurant to the randomizer list.
        arand/asr  -> standard
        assr       -> special
        """
        validate = self.role_validate(ctx.author.roles)
        if not validate:
            await self.send_embed(ctx, "Permission Denied", "❌ You need to be a Moderator to use this command.", discord.Color.red())
            return
        
        name = " ".join(args).strip()
        if not name:
            await self.send_embed(
                ctx,
                "Invalid Usage",
                "⚠️ Please provide a restaurant name to add.\n\n"
                "Usage: `!arand <restaurant_name>` for standard or `!assr <restaurant_name>` for special.",
                discord.Color.orange(),
            )
            return
        if not self.client:
            await self.send_embed(ctx, "Database Error", "❌ Cannot connect to the database.", discord.Color.red())
            return
        
        invoked = (ctx.invoked_with or "").lower()
        rtype = "sr" if invoked in ("arand", "asr") else "ssr"

        if name in [i["restaurant"] for i in self.collection.find({"type": rtype})]:
            await self.send_embed(
                ctx,
                "Already Exists",
                f"⚠️ **{name}** is already in the {'**special** ' if rtype == 'ssr' else ''}randomizer list.",
                discord.Color.orange(),
            )
            return
        doc = [
            {"restaurant": i, "type": rtype} for i in name.split()
        ]
        self.collection.insert_many(doc)

        await self.send_embed(
            ctx,
            "Added to Randomizer",
            f"✅ Added **{name}** to the {'**special** ' if rtype == 'ssr' else ''}randomizer list.",
            discord.Color.green(),
            footer=f"Use `tsr` for standard pick or `tssr` for special pick.",
        )

    @commands.command(name="nrand", aliases=["sr"])
    async def rand(self, ctx: commands.Context):
        """Pick a random restaurant from standard list."""
        results = list(self.collection.find({"type": "sr"}))
        if not results:
            await self.send_embed(
                ctx,
                "No Choices",
                "⚠️ No **standard** restaurant choices available.",
                discord.Color.orange(),
                footer="Add one with !asr <name>",
            )
            return

        choice = random.choice(results)
        await self.send_embed(
            ctx,
            "Today's Pick (Standard)",
            f"🍽️ **{choice['restaurant']}** 🎉",
            discord.Color.purple(),
        )

    @commands.command(name="srand", aliases=["ssr"])
    async def special_rand(self, ctx: commands.Context):
        """Pick a random restaurant from special list."""
        results = list(self.collection.find({"type": "ssr"}))
        if not results:
            await self.send_embed(
                ctx,
                "No Choices",
                "⚠️ No **special** restaurant choices available.",
                discord.Color.orange(),
                footer="Add one with tassr <name>",
            )
            return

        choice = random.choice(results)
        await self.send_embed(
            ctx,
            "Today's Pick (Special)",
            f"🍽️ **{choice['restaurant']}** 🎉",
            discord.Color.yellow(),
        )
        
    @commands.command(name="lrand", aliases=["ls"])
    async def list_rand(self, ctx: commands.Context):
        if not self.client:
            return await self.send_embed(ctx, "Database Error", "❌ Cannot connect to the database.", discord.Color.red())
        cursor = self.collection.find(
            {"restaurant": {"$exists": True, "$type": "string", "$ne": ""}},
            {"_id": 0, "restaurant": 1, "type": 1},
        )
        docs = list(cursor)
        sr = sorted([d["restaurant"] for d in docs if d.get("type") == "sr"], key=str.casefold)
        ssr = sorted([d["restaurant"] for d in docs if d.get("type") == "ssr"], key=str.casefold)

        def bullets(items: list[str]) -> str:
            return "\n".join(f"• {name}" for name in items)

        def chunk_text(text: str, maxlen: int = 1024) -> list[str]:
            if len(text) <= maxlen:
                return [text]
            parts, buf, total = [], [], 0
            for line in text.splitlines(True):
                if total + len(line) > maxlen and buf:
                    parts.append("".join(buf).rstrip())
                    buf, total = [line], len(line)
                else:
                    buf.append(line)
                    total += len(line)
            if buf:
                parts.append("".join(buf).rstrip())
            return parts

        async def send_list_embed(title: str, color: discord.Color, items: list[str], empty_msg: str):
            if not items:
                embed = discord.Embed(
                    title=title,
                    description=f"⚠️ {empty_msg}",
                    color=discord.Color.orange(),
                    timestamp=ctx.message.created_at,
                )
                embed.set_author(name=str(ctx.author), icon_url=getattr(ctx.author.display_avatar, "url", discord.Embed))
                embed.set_footer(text="Tip: add with (t,b)asr <name> or (t,b)assr <name>")
                async with ctx.typing():
                    await asyncio.sleep(DELAY_SEC)
                    return await ctx.send(embed=embed)
            text = bullets(items)
            parts = chunk_text(text)
            embed = discord.Embed(
                title=f"{title} ({len(items)})",
                description="",
                color=color,
                timestamp=ctx.message.created_at,
            )
            embed.set_author(name=str(ctx.author), icon_url=getattr(ctx.author.display_avatar, "url", discord.Embed))
            # first chunk as a field
            for i, part in enumerate(parts, start=1):
                name = "List" if i == 1 else "Continued"
                embed.add_field(name=name, value=part, inline=False)
            embed.set_footer(text="Use tdrand <name> to delete • tsr / tssr to pick")
            async with ctx.typing():
                await asyncio.sleep(DELAY_SEC)
                await ctx.send(embed=embed)

        await send_list_embed("🍱 Standard Restaurants", discord.Color.purple(), sr, "No standard restaurants found.")
        await send_list_embed("⭐ Special Restaurants", discord.Color.gold(), ssr, "No special restaurants found.")


    @commands.command(name="drand", aliases=["dres"])
    async def del_rand(self, ctx: commands.Context, * , name: str = None):
        """Delete a restaurant from either list by exact name."""
        if not name:
            await self.send_embed(
                ctx,
                "Invalid Usage",
                "⚠️ Please provide a restaurant name to delete.\n\n"
                "Usage: `!drand <restaurant_name>`",
                discord.Color.orange(),
            )
            return
        validate = self.role_validate(ctx.author.roles)
        if not validate:
            await self.send_embed(ctx, "Permission Denied", "❌ You need to be a Moderator to use this command.", discord.Color.red())
            return
        if not self.client:
            await self.send_embed(ctx, "Database Error", "❌ Cannot connect to the database.", discord.Color.red())
            return
        result = self.collection.delete_one({"restaurant": name})
        if result.deleted_count == 0:
            await self.send_embed(
                ctx,
                "Not Found",
                f"⚠️ **{name}** was not found in the randomizer list.",
                discord.Color.orange(),
            )
        else:
            await self.send_embed(
                ctx,
                "Deleted",
                f"✅ Removed **{name}** from the randomizer list.",
                discord.Color.green(),
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Randomizer(bot))
