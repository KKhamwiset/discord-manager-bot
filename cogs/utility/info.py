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
                commands_list = cog.get_commands()
                if not commands_list:
                    continue

                visible_commands = [c for c in commands_list if not c.hidden]
                if not visible_commands:
                    continue

                command_names = [f"`{c.name} {"(" + ', '.join(c.aliases) + ")" if c.aliases else ''}`" for c in visible_commands]
                cog_icon = self.emoji.get(cog_name, "📂")
                
                embed.add_field(
                    name=f"{cog_icon} {cog_name}", 
                    value=", ".join(command_names), 
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

        cmd = self.bot.get_command(command_name)

        if cmd is None:
            return await ctx.send(f"❌ Command `{command_name}` not found.")

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