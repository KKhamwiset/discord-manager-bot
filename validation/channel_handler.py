import discord
from discord.ext import commands

async def global_channel_check(ctx: commands.Context) -> bool:
    if ctx.guild is None:
        return True
    
    collection = ctx.bot.db["guild_config"]
    doc = await collection.find_one({"_id": ctx.guild.id})

    if not doc or doc.get("mode", "all") == "all":
        return True

    allowed = doc.get("allowed_channels", [])
    if ctx.channel.id in allowed or ctx.command.name == "setbotchannel":
        return True

    await ctx.send(
        embed=discord.Embed(
            title="🚫 Commands not allowed here",
            description="Please use bot commands in the designated bot channel.",
            color=discord.Color.red(),
        )
    )
    return False