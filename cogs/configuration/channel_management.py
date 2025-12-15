import discord
import validation
from discord import app_commands
from discord.ext import commands
from typing import Literal, Optional, Any, Dict, List

# --- Utility Functions ---

def create_embed(title: str, description: str, color: discord.Color) -> discord.Embed:
    """Creates a standardized Discord embed."""
    return discord.Embed(title=title, description=description, color=color)

def get_channel_entry_index(allowed_channels: List[Dict[str, Any]], channel_id: int) -> Optional[int]:
    """Finds the index of a channel entry in the allowed_channels list."""
    try:
        return next(
            (i for i, ch in enumerate(allowed_channels) if ch.get("channel_id") == channel_id)
        )
    except StopIteration:
        return None

# --- Cog Logic ---

class ChannelManagement(commands.Cog):
    """
    Commands for managing which channels the bot is allowed to be used in.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        try:
            self.collection = bot.db["guild_config"]
            print("✅ ChannelManagement Cog connection, OK.")
        except Exception as e:
            print(f"❌ ChannelManagement Cog connection failed: {e!r}")

    async def _get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        doc = await self.collection.find_one({"_id": guild_id})
        return doc if doc is not None else {}

    async def _check_guild_context(self, ctx: commands.Context) -> Optional[discord.Guild]:
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server.")
            return None
        return ctx.guild

    async def _validate_commands(self, ctx: commands.Context, raw_names: List[str]):
        names = []
        aliases = []
        invalid = []

        for n in raw_names:
            tester = self.bot.get_command(n)
            if tester is None:
                invalid.append(n)
            else:
                names.append(tester.qualified_name)
                aliases.extend([a for a in tester.aliases if a not in aliases])
        
        unique_names = list(dict.fromkeys(names))
        
        if invalid:
            error_msg = "❌ These commands were not found: " + ", ".join(f"`{c}`" for c in invalid)
            await ctx.send(error_msg)

        return unique_names, aliases, invalid


    # --- disablebotchannel command ---

    @validation.role()
    @commands.hybrid_command(
        name="disablebotchannel",
        description="Disable the bot from responding to commands in this channel.",
        help="Disable this channel as an allowed bot channel."
    )
    async def disable_bot_channel(self, ctx: commands.Context):
        guild = await self._check_guild_context(ctx)
        if guild is None:
            return

        channel = ctx.channel
        config = await self._get_guild_config(guild.id)
        # Removed unnecessary ": List[Dict[str, Any]]" hint
        allowed_channels = config.get("allowed_channels", [])
        
        idx = get_channel_entry_index(allowed_channels, channel.id)
        critical = False
        
        if idx is not None:
            allowed_channels.pop(idx)

            if not allowed_channels:
                critical = True
                update_fields = {
                    "mode": "all",
                    "allowed_channels": [],
                }
                
                await self.collection.update_one(
                    {"_id": guild.id},
                    {"$set": update_fields},
                    upsert=True,
                )
                
                description = (
                    f"{channel.mention} removed from bot channels.\n"
                    "Commands are now allowed in **all channels** again."
                )
                embed = create_embed(
                    "🔁 Bot channel restriction disabled",
                    description,
                    discord.Color.orange()
                )
            else:
                await self.collection.update_one(
                    {"_id": guild.id},
                    {"$set": {"allowed_channels": allowed_channels}},
                    upsert=True,
                )
                
                description = f"{channel.mention} removed from allowed bot channels."
                embed = create_embed(
                    "✅ Bot channel disabled",
                    description,
                    discord.Color.green()
                )
            
            moderator_role = discord.utils.find(lambda r: r.name == 'Moderator', guild.roles)
            mention = moderator_role.mention if critical and moderator_role else ""
            
            await ctx.send(content=mention, embed=embed)
            
        else:
            description = f"{channel.mention} is not an allowed bot channel."
            embed = create_embed(
                "⚠️ Channel not found",
                description,
                discord.Color.red()
            )
            await ctx.send(embed=embed)

    # # --- allcommandsallowed command ---
    # @validation.role()
    # @commands.hybrid_command(
    #     name="allchannelallowed",
    #     description="Set the bot to allow commands in all channels (disable restrictions).",
    #     help="Allow bot commands in all channels."
    # )
    # async def all_channel_allowed(self, ctx: commands.Context , name  = None):
    #     guild = await self._check_guild_context(ctx)
    #     if guild is None:
    #         return
    #     if name is None:
    #         await ctx.send("❌ Please provide a name for the configuration.")
    #         return
        
    #     config = await self._get_guild_config(guild.id)
        
    #     if config.get("mode", "all") == "all":
    #         await ctx.send("📢 Bot commands are already allowed in **all channels**.")
    #         return
    #     all_channels = []
    #     cmd = self.bot.get_command(name)
    #     if cmd is None:
    #         await ctx.send(f"❌ Command `{name}` not found.")
    #         return
    #     for channel in ctx.guild.text_channels:
    #         channel_config = next((
    #             (ch for ch in config.get("allowed_channels", []) if ch.get("channel_id") == channel.id)
    #         ), None)
    #         if channel_config and channel_config.get("cmd_mode") == "all" :
    #             continue
    #         all_channels.append({
    #             "channel_id": channel.id,
    #             "cmd_mode": "only",
    #             "allowed_commands": [
    #                 cmd.qualified_name,
    #                 *cmd.aliases
    #             ],
    #         })
    #         for thread in channel.threads:
    #             all_channels.append({
    #                 "channel_id": thread.id,
    #                 "cmd_mode": "only",
    #                 "allowed_commands": [
    #                     cmd.qualified_name,
    #                     *cmd.aliases
    #                 ],
    #             })
    #     await self.collection.update_one(
    #         {"_id": guild.id},
    #                 {
    #                     "$set": {
    #                         "mode": "whitelist",
    #                     },
    #                     "$addToSet": {
    #                         "allowed_channels": {
    #                             "$each": all_channels
    #                         }
    #                     }
    #                 },
    #                 upsert=True,
    #         )
    #     await ctx.send(f"✅ {name} commands are now allowed in **all channels**.")


    
    # --- setbotchannel command ---
    @validation.role()
    @commands.hybrid_command(
        name="setbotchannel", 
        description="Configure which commands are allowed in this channel.",
        help="Set this channel as a bot channel"
    )
    @app_commands.describe(
        cmd_mode="Filter mode: 'all' (allow everything), 'only' (whitelist), or 'exclude' (blacklist).",
        cmd_names="List of command names separated by spaces (e.g. 'ping help'). Required for 'only'/'exclude'."
    )
    async def set_bot_channel(
        self,
        ctx: commands.Context,
        cmd_mode: Literal["all", "only", "exclude"] = "all",
        *,
        cmd_names: Optional[str] = None,
    ):
        guild = await self._check_guild_context(ctx)
        if guild is None:
            return

        channel = ctx.channel
        
        raw_names = cmd_names.split() if cmd_names else []
        names, aliases, invalid = await self._validate_commands(ctx, raw_names)

        if invalid and len(invalid) == len(raw_names):
             return
             
        if cmd_mode in ("only", "exclude") and not names:
            error_msg = (
                "❌ You must provide at least **one command name** when using "
                "`only` or `exclude`.\n"
                "**Example:**\n"
                "`!setbotchannel only ping help`\n"
                "**Slash:** `/setbotchannel cmd_mode:only cmd_names:\"ping help\"`"
            )
            await ctx.send(error_msg)
            return

        if cmd_mode == "all" and raw_names:
            error_msg = (
                "❌ You cannot provide command names when mode is `all`.\n"
                "If you want to filter commands, use `only` or `exclude`."
            )
            await ctx.send(error_msg)
            return

        config = await self._get_guild_config(guild.id)
        allowed_channels = config.get("allowed_channels", [])

        idx = get_channel_entry_index(allowed_channels, channel.id)
        
        new_entry = {
            "channel_id": channel.id,
            "cmd_mode": cmd_mode,
            "allowed_commands": names if cmd_mode != "all" else []
        }
        
        if idx is not None:
            allowed_channels[idx] = new_entry
            update_data = {"$set": {f"allowed_channels.{idx}": new_entry}}
            title = "✅ Channel updated"
        else:
            allowed_channels.append(new_entry)
            update_data = {
                "$set": {
                    "mode": "whitelist",
                    "allowed_channels": allowed_channels,
                }
            }
            title = "✅ Channel enabled"

        await self.collection.update_one(
            {"_id": guild.id},
            update_data,
            upsert=True,
        )
        
        if cmd_mode == "all":
            detail = "Mode: **all** (All commands allowed)"
        elif cmd_mode == "only":
            detail = (
                "Mode: **only** (Whitelist)\n"
                f"Allowed: `{', '.join(names)}`"
                + (f" | Aliases: `{', '.join(aliases)}`" if aliases else "")
            )
        else:
            detail = (
                "Mode: **exclude** (Blacklist)\n"
                f"Blocked: `{', '.join(names)}`"
                + (f" | Aliases: `{', '.join(aliases)}`" if aliases else "")
            )

        description = f"{channel.mention} bot channel settings {'updated' if idx is not None else 'configured'}.\n{detail}"

        embed = create_embed(title, description, discord.Color.green())
        await ctx.send(embed=embed)

    # --- listbotchannels command ---

    @validation.role()
    @commands.hybrid_command(
        name="listbotchannels", 
        description="List all channels where bot commands are explicitly allowed/configured.",
        help="Show allowed bot channels"
    )
    async def list_bot_channels(self, ctx: commands.Context):
        guild = await self._check_guild_context(ctx)
        if guild is None:
            return

        config = await self._get_guild_config(guild.id)
        
        if config.get("mode", "all") == "all":
            await ctx.send("📢 Bot commands are allowed in **all** channels (Default Mode).")
            return

        # Removed unnecessary ": List[Dict[str, Any]]" hint
        entries = config.get("allowed_channels", [])
        if not entries:
            await ctx.send("⚠️ Whitelist mode is active, but no channels are configured. Bot may be silent.")
            return

        # Removed unnecessary ": List[str]" hint
        lines = []
        for entry in entries:
            ch_id = int(entry.get("channel_id"))
            ch = guild.get_channel(ch_id) or guild.get_thread(ch_id) 
            
            if ch is None:
                continue

            cmode = entry.get("cmd_mode", "all")
            cmds = entry.get("allowed_commands", []) or []

            if cmode == "all":
                detail = "All commands"
            elif cmode == "only":
                detail = "Only: " + (", ".join(cmds) if cmds else "(None)")
            elif cmode == "exclude":
                detail = "All except: " + (", ".join(cmds) if cmds else "(None)")
            else:
                detail = f"{cmode} (raw)"

            lines.append(f"{ch.mention} — `{detail}`")

        await ctx.send(
            embed=create_embed(
                "📋 Allowed Bot Channels",
                "\n".join(lines),
                discord.Color.blue(),
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelManagement(bot))