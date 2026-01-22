import random
import asyncio
import discord
import re
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
    def _filtering(self, name: str, exclude: list[str]) -> bool:
        """Helper to check if name matches any exclude patterns."""
        candidate = []
        for ex in exclude:
            if re.search(re.escape(ex), name, re.IGNORECASE):
                return True
            candidate.append(name)
        return candidate
    
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

    async def get_guild_doc(self, guild_id: str):
        """Helper to get the guild document, ensuring the array exists."""
        return await self.col.find_one({"guild_id": guild_id})

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
        guild_id = str(ctx.guild.id)
        exists = await self.col.find_one({
            "guild_id": guild_id,
            "restaurant": {
                "$elemMatch": {
                    "restaurant": {"$regex":f"^{re.escape(name)}$", "$options": "i"}, 
                    "type": rtype
                }
            }
        })

        if exists:
            return await self.send_embed(
                ctx,
                "Already Exists",
                f"⚠️ **{name}** is already in the "
                f"{'**special** ' if rtype == 'ssr' else ''}list.",
                discord.Color.orange(),
            )

        await self.col.update_one(
            {"guild_id": guild_id},
            {
                "$push": {"restaurant": {"restaurant": name, "type": rtype}}
            },
            upsert=True
        )

        await self.send_embed(
            ctx,
            "Added",
            f"✅ Added **{name}** to the "
            f"{'**special** ' if rtype == 'ssr' else ''}randomizer list.",
            discord.Color.green(),
        )

    @commands.command(name="nrand", aliases=["sr","ssr"], help="Pick a random restaurant.")
    async def rand(self, ctx: commands.Context, *exclude: str):
        """Pick a random restaurant from list."""
        guild_id = str(ctx.guild.id)
        
        if exclude is None:
            exclude = []
        else:
            exclude_str = ' '.join(list(exclude))
            if ':' in exclude_str:
                exclude = exclude_str.split(":")[-1].split()
            else:
                exclude = []

        doc = await self.get_guild_doc(guild_id)
        if not doc or "restaurant" not in doc:
            return await self.send_embed(
                ctx, "No Choices", "⚠️ No restaurants found for this server.", discord.Color.orange()
            )

        candidates = []

        invoke_with = ctx.invoked_with.lower()
        is_ssr = invoke_with == "ssr"
        type_selection =  lambda item: item.get("type") == "ssr" if is_ssr else item.get("type") == "sr"

        for item in doc["restaurant"]:
            if type_selection(item):
                r_name = item.get("restaurant", "")
                is_excluded = False
                for ex in exclude:
                    if re.search(re.escape(ex), r_name, re.IGNORECASE):
                        is_excluded = True
                        break
                
                if not is_excluded:
                    candidates.append(r_name)

        if not candidates:
            return await self.send_embed(
                ctx,
                "No Choices",
                "⚠️ No **standard** restaurants available (or all were excluded).",
                discord.Color.orange(),
                footer="Add one with !arand <name>",
            )

        picked = random.choice(candidates)

        await self.send_embed(
            ctx,
            "Today's Pick (Standard)",
            f"🍽️ **{picked}** 🎉",
            discord.Color.purple(),
        )


    @commands.command(name="lrand", aliases=["ls"], help="List all restaurants by type.")
    async def list_rand(self, ctx: commands.Context):
        """List all restaurants by type."""
        guild_id = str(ctx.guild.id)
        doc = await self.get_guild_doc(guild_id)
        
        sr_list = []
        ssr_list = []

        if doc and "restaurant" in doc:
            for item in doc["restaurant"]:
                name = item.get("restaurant", "Unknown")
                if item.get("type") == "sr":
                    sr_list.append(name)
                elif item.get("type") == "ssr":
                    ssr_list.append(name)

        sr = sorted(sr_list, key=str.casefold)
        ssr = sorted(ssr_list, key=str.casefold)

        # Helper functions for Embeds (Same as your old code)
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

    
    @commands.command(name="drand", aliases=["dres"], help="Delete a randomizer entry by name.")
    @validation.role()
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
        
        guild_id = str(ctx.guild.id)
        
        result = await self.col.update_one(
            {"guild_id": guild_id},
            {"$pull": {"restaurant": {"restaurant": name}}}
        )

        if result.modified_count == 0:
            await self.send_embed(
                ctx,
                "Not Found",
                f"⚠️ **{name}** was not found in the randomizer list (or DB error).",
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