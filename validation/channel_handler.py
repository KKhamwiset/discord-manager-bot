from discord.ext import commands
import discord

async def global_channel_check(ctx: commands.Context) -> bool:

    if isinstance(ctx.channel, discord.Thread):
        if ctx.channel.me is None:
            return False
    
    if ctx.guild is None:
        return True

    if ctx.command is None:
        return True

    if ctx.command.name in ["command-add"
                        , "channel-configure"
                        , "channel-remove"
                        , "channel-list"
                        , "help"
                        , "command-allow-all"
                        , "info"]:
        return True
    
    collection = ctx.bot.db["guild_config"]
    doc = await collection.find_one({"_id": str(ctx.guild.id)})
    if not doc:
        return True

    if doc.get("mode", "all") == "all":
        return True

    allowed_channels = doc.get("allowed_channels", [])

    chan_cfg = next(
        (c for c in allowed_channels if c.get("channel_id") == str(ctx.channel.id)),
        None,
    )
    if chan_cfg is None:
        await ctx.send(
            embed=discord.Embed(
                title="🚫 Commands not allowed in this channel",
                description="This channel is not configured for bot commands.",
                color=discord.Color.red(),
            )
        )
        return False

    cmd_mode = chan_cfg.get("cmd_mode", "all")
    command_list = chan_cfg.get("allowed_commands", []) or []


    cmd_names = [ctx.command.qualified_name, *ctx.command.aliases]


    if cmd_mode == "all":
        return True

    if cmd_mode == "only":
        if any(name in command_list for name in cmd_names):
            return True

        await ctx.send(
            embed=discord.Embed(
                title="🚫 Command not allowed here",
                description=(
                    f"`{ctx.invoked_with}` is not enabled in {ctx.channel.mention}.\n"
                    "ขอให้ใช้คำสั่งนี้ในช่องที่อนุญาตเท่านั้นครับ"
                ),
                color=discord.Color.red(),
            )
        )
        return False


    if cmd_mode == "exclude":
        if any(name in command_list for name in cmd_names):
            await ctx.send(
                embed=discord.Embed(
                    title="🚫 Command blocked in this channel",
                    description=(
                        f"`{ctx.invoked_with}` is disabled in {ctx.channel.mention}."
                    ),
                    color=discord.Color.red(),
                )
            )
            return False
        return True
    
    await ctx.send(
        embed=discord.Embed(
            title="⚠️ Channel config error",
            description="Channel has an unknown command mode; blocking for safety.",
            color=discord.Color.orange(),
        )
    )
    return False
