import discord
import validation
from discord.ext import commands

class ChannelManagement(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        try:
            self.collection = bot.db["guild_config"]
            print("✅ ChannelManagement Cog connection, OK.")
        except Exception as e:
            print(f"❌ ChannelManagement Cog connection failed")


    @validation.role()
    @commands.hybrid_command(
        name="setbotchannel",
        help="Toggle this channel as an allowed bot channel",
    )
    async def set_bot_channel(self, ctx: commands.Context):
        guild = ctx.guild
        channel = ctx.channel

        if guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return

        doc = await self.collection.find_one({"_id": guild.id})

        if doc and doc.get("mode") == "whitelist":
            allowed = doc.get("allowed_channels", [])
        else:
            allowed = []

        if channel.id in allowed:
            allowed.remove(channel.id)
            if not allowed:
                await self.collection.update_one(
                    {"_id": guild.id},
                    {"$set": {"mode": "all", "allowed_channels": []}},
                    upsert=True,
                )
                await ctx.send(
                    embed=discord.Embed(
                        title="🔁 Bot channel restriction disabled",
                        description=(
                            f"{channel.mention} removed from bot channels.\n"
                            "Commands are now allowed in **all channels** again."
                        ),
                        color=discord.Color.orange(),
                    )
                )
            else:
                await self.collection.update_one(
                    {"_id": guild.id},
                    {
                        "$set": {
                            "mode": "whitelist",
                            "allowed_channels": allowed,
                        }
                    },
                    upsert=True,
                )
                await ctx.send(
                    embed=discord.Embed(
                        title="🚫 Channel disabled",
                        description=f"{channel.mention} is no longer an allowed bot channel.",
                        color=discord.Color.red(),
                    )
                )
        else:
            allowed.append(channel.id)
            await self.collection.update_one(
                {"_id": guild.id},
                {
                    "$set": {
                        "mode": "whitelist",
                        "allowed_channels": allowed,
                    }
                },
                upsert=True,
            )
            await ctx.send(
                embed=discord.Embed(
                    title="✅ Channel enabled",
                    description=f"{channel.mention} is now an allowed bot channel.",
                    color=discord.Color.green(),
                )
            )

    @validation.role()
    @commands.hybrid_command(
        name="addbotchannel",
        help="Allow another bot channel (or all except this one with exclude=True)",
    )
    async def add_bot_channel(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        exclude: bool = False,
    ):
        if channel.guild is None or channel.guild.id != ctx.guild.id:
            await ctx.send("❌ Please select a channel from this server.")
            return

        if exclude:
            allowed_ids = [
                ch.id for ch in ctx.guild.text_channels
                if ch.id != channel.id
            ]
            await self.collection.update_one(
                {"_id": ctx.guild.id},
                {
                    "$set": {
                        "mode": "whitelist",
                        "allowed_channels": allowed_ids,
                    }
                },
                upsert=True,
            )
            await ctx.send(
                embed=discord.Embed(
                    title="✅ Bot channels updated",
                    description=(
                        f"Commands are now allowed in **all text channels** "
                        f"except {channel.mention}."
                    ),
                    color=discord.Color.green(),
                )
            )
            return

        await self.collection.update_one(
            {"_id": ctx.guild.id},
            {
                "$set": {"mode": "whitelist"},
                "$addToSet": {"allowed_channels": channel.id},
            },
            upsert=True,
        )
        await ctx.send(f"✅ Added {channel.mention} to allowed bot channels.")

    @validation.role()
    @commands.hybrid_command(name="listbotchannels", help="Show allowed bot channels")
    async def list_bot_channels(self, ctx: commands.Context):
        doc = await self.collection.find_one({"_id": ctx.guild.id})
        if not doc or doc.get("mode", "all") == "all":
            await ctx.send("📢 Bot commands are allowed in **all** channels.")
            return

        ids = doc.get("allowed_channels", [])
        if not ids:
            await ctx.send("⚠️ Whitelist mode is on but no channels are set.")
            return

        channels = [ctx.guild.get_channel(cid) for cid in ids]
        mentions = [c.mention for c in channels if c is not None]
        await ctx.send("📜 Allowed bot channels:\n" + "\n".join(mentions))


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelManagement(bot))
