import discord
import os
from discord.ext import commands
from discord import app_commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji = {
            "Core": "⚙️",
            "HomeworkManager": "📚",
            "Schedule": "📅",
            "ChannelManagement": "📺",
            "Maintenance": "🔧",
            "RoleManagement": "🛡️",
            "Info": "ℹ️",
            "Randomizer": "🎲"
        }

    @commands.command(help="Show bot/server info")
    async def info(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Bot Info",
            description="General เบ๊ Bot - Your Discord Utility Assistant",
            color=discord.Color.blue()
        )
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.add_field(name="Current bot instance ", value=self.bot.instance, inline=False)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
        embed.add_field(name="Server", value=ctx.guild.name if ctx.guild else "DM", inline=True)
        embed.add_field(name="Users", value=str(len(self.bot.users)), inline=True)
        embed.set_footer(text=f"Requested by {ctx.author.name}")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="help", description="Show the help menu or details for a specific command")
    @app_commands.describe(command_name="The name of the command you want to check")
    async def help(self, ctx: commands.Context, command_name: str | None = None):
        if command_name is None:
            embed = discord.Embed(
                title="🤖 Bot Help Menu",
                description=f"Prefixes: **`b`** or **`t`** (or mention me).\nUse `{ctx.clean_prefix}help <command>` for details.",
                color=discord.Color.blurple(),
            )
            if ctx.author.avatar:
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

            for cog_name, cog in self.bot.cogs.items():
                text_cmds = cog.get_commands()
                slash_cmds = cog.get_app_commands()

                if not text_cmds and not slash_cmds:
                    continue

                command_display_list = []
                seen_commands = set()
                for c in text_cmds:
                    if not c.hidden:
                        name_str = f"`{c.name} {'(' + ', '.join(c.aliases) + ')' if c.aliases else ''}`"
                        command_display_list.append(name_str)
                        seen_commands.add(c.name)

                for c in slash_cmds:
                    if c.name not in seen_commands:
                        command_display_list.append(f"`/{c.name}`")
                
                if not command_display_list:
                    continue

                cog_icon = self.emoji.get(cog_name, "📂")
                
                embed.add_field(
                    name=f"{cog_icon} {cog_name}", 
                    value=", ".join(command_display_list), 
                    inline=False
                )

            uncogged_commands = [c for c in self.bot.commands if c.cog is None and not c.hidden]
            if uncogged_commands:
                command_names = [f"`{c.name}`" for c in uncogged_commands]
                embed.add_field(
                    name="🧩 Uncategorized",
                    value=", ".join(command_names),
                    inline=False
                )

            embed.set_footer(text=f"Requested by {ctx.author.name}")
            return await ctx.send(embed=embed)

        # --- Specific Command Help Logic ---
        
        # Check text commands first
        cmd = self.bot.get_command(command_name)
        
        # If not found, check if it's a slash command in the tree
        if cmd is None:
            for command in self.bot.tree.walk_commands():
                if command.name == command_name:
                    embed = discord.Embed(
                        title=f"❓ Help: /{command.name}",
                        description=command.description or "No description provided.",
                        color=discord.Color.blurple(),
                    )
                    embed.add_field(name="Usage", value=f"`/{command.name}`", inline=False)
                    return await ctx.send(embed=embed)
            
            # If still not found
            return await ctx.send(f"❌ Command `{command_name}` not found.")

        # Text Command Help Embed
        embed = discord.Embed(
            title=f"❓ Help: {ctx.clean_prefix}{cmd.qualified_name}",
            description=cmd.help or "No description provided.",
            color=discord.Color.blurple(),
        )

        usage = f"{ctx.clean_prefix}{cmd.qualified_name} {cmd.signature}".strip()
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)

        if cmd.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in cmd.aliases),
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))