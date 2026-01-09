import random
import asyncio
import discord
from discord.ext import commands
import validation
DELAY_SEC = 0.2


class Randomizer(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.col = self.bot.db["restaurant_choices"]
        if self.col is not None:
            print("✅ Randomizer Cog connection, OK.")
        else:
            print("❌ Randomizer Cog connection failed.")

    # ---------- util ----------

    async def send_embed(
        self,
        ctx: commands.Context,
        title: str,
        description: str,
        color: discord.Color = discord.Color.blurple(),
        footer: str | None = None,
    ):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_author(
            name=str(ctx.author),
            icon_url=getattr(ctx.author.display_avatar, "url", discord.Embed),
        )
        if footer:
            embed.set_footer(text=footer)
        async with ctx.typing():
            await asyncio.sleep(DELAY_SEC)
            await ctx.send(embed=embed)

    # ---------- commands ----------
    @commands.command(
        name="arand",
        aliases=["asr", "asrand", "assr"],
        help="Add a restaurant to the randomizer list. \n **arand** for standard or **asrand** for special.",
    )
    @validation.role()
    async def add_rand(self, ctx: commands.Context, *args):
        """Add a restaurant to the randomizer list (standard or special)."""

        name = " ".join(args).strip()
        if not name:
            return await self.send_embed(
                ctx,
                "Invalid Usage",
                "⚠️ Please provide a restaurant name to add.\n\n"
                "Usage: `!arand <name>` for standard or `!assr <name>` for special.",
                discord.Color.orange(),
            )

        invoked = (ctx.invoked_with or "").lower()
        rtype = "sr" if invoked in ("arand", "asr") else "ssr"

        exists = await self.col.find_one({"type": rtype, "restaurant": name})
        if exists:
            return await self.send_embed(
                ctx,
                "Already Exists",
                f"⚠️ **{name}** is already in the "
                f"{'**special** ' if rtype == 'ssr' else ''}list.",
                discord.Color.orange(),
            )

        await self.col.insert_one({"type": rtype, "restaurant": name})
        await self.send_embed(
            ctx,
            "Added",
            f"✅ Added **{name}** to the "
            f"{'**special** ' if rtype == 'ssr' else ''}randomizer list.",
            discord.Color.green(),
        )

    @commands.command(name="nrand", aliases=["sr"], help="Pick a random standard restaurant.")
    async def rand(self, ctx: commands.Context, *exclude: str):
        import re
        if exclude is None:
            exclude = []
        else:
            exclude = ' '.join(list(exclude))
        """Pick a random restaurant from standard list."""
        exclude = exclude.split(":")[-1].split() if exclude else []

        match = {"type": "sr"}
        if exclude:
            escaped = [re.escape(x) for x in exclude]
            match["restaurant"] = {
                "$not": {
                    "$regex": "|".join(escaped),
                    "$options": "i"
                }
            }

        picked = await self.col.aggregate(
            [
                {"$match": match},
                {"$sample": {"size": 1}},
            ]
        ).to_list(length=1)
        if not picked:
            return await self.send_embed(
                ctx,
                "No Choices",
                "⚠️ No **standard** restaurants available.",
                discord.Color.orange(),
                footer="Add one with !asr <name>",
            )

        await self.send_embed(
            ctx,
            "Today's Pick (Standard)",
            f"🍽️ **{picked[0]['restaurant']}** 🎉",
            discord.Color.purple(),
        )

    @commands.command(name="srand", aliases=["ssr"], help="Pick a random special restaurant.")
    async def special_rand(self, ctx: commands.Context):
        """Pick a random restaurant from special list."""
        picked = await self.col.aggregate(
            [
                {"$match": {"type": "ssr"}},
                {"$sample": {"size": 1}},
            ]
        ).to_list(length=1)

        if not picked:
            return await self.send_embed(
                ctx,
                "No Choices",
                "⚠️ No **special** restaurants available.",
                discord.Color.orange(),
                footer="Add one with !assr <name>",
            )

        await self.send_embed(
            ctx,
            "Today's Pick (Special)",
            f"🍽️ **{picked[0]['restaurant']}** 🎉",
            discord.Color.yellow(),
        )

    @commands.command(name="lrand", aliases=["ls"], help="List all restaurants by type.")
    async def list_rand(self, ctx: commands.Context):
        """List all restaurants by type."""
        cursor = self.col.find(
            {"restaurant": {"$exists": True, "$type": "string", "$ne": ""}},
            {"_id": 0, "restaurant": 1, "type": 1},
        )
        docs = [d async for d in cursor]
        sr = sorted([d["restaurant"] for d in docs if d["type"] == "sr"], key=str.casefold)
        ssr = sorted([d["restaurant"] for d in docs if d["type"] == "ssr"], key=str.casefold)

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
                return await self.send_embed(
                    ctx, title, f"⚠️ {empty_msg}", discord.Color.orange()
                )

            text = bullets(items)
            parts = chunk_text(text)
            embed = discord.Embed(
                title=f"{title} ({len(items)})",
                color=color,
                timestamp=ctx.message.created_at,
            )
            embed.set_author(
                name=str(ctx.author),
                icon_url=getattr(ctx.author.display_avatar, "url", discord.Embed),
            )
            for i, part in enumerate(parts, start=1):
                embed.add_field(name=("List" if i == 1 else "Continued"), value=part, inline=False)
            embed.set_footer(text="Use tdrand <name> to delete • tsr / tssr to pick")
            async with ctx.typing():
                await asyncio.sleep(DELAY_SEC)
                await ctx.send(embed=embed)

        await send_list_embed("🍱 Standard Restaurants", discord.Color.purple(), sr, "No standard restaurants found.")
        await send_list_embed("⭐ Special Restaurants", discord.Color.gold(), ssr, "No special restaurants found.")

    @validation.role()
    @commands.command(name="drand", aliases=["dres"], help="Delete a randomizer entry by name.")
    async def del_rand(self, ctx: commands.Context, *, name: str | None = None):
        """Delete a restaurant by exact name."""
        if not name:
            return await self.send_embed(
                ctx,
                "Invalid Usage",
                "⚠️ Please provide a restaurant name to delete.\n\n"
                "Usage: `!drand <restaurant_name>`",
                discord.Color.orange(),
            )

        result = await self.col.delete_one({"restaurant": name})
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
