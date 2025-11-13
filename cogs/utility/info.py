import discord
from discord.ext import commands

class Info(commands.Cog):
    def __init__(self,bot):
        self.bot = bot 

    @commands.command(help="Show bot/server info")
    async def info(self ,ctx: commands.Context):
        embed = discord.Embed(
            title="Bot Info",
            description="This is a simple info command using embeds!",
            color=discord.Color.blue()
        )
        if ctx.author.avatar:
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        if ctx.bot.user and ctx.bot.user.avatar:
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=False)
        embed.add_field(name="Server", value=ctx.guild.name if ctx.guild else "DM", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name}")

        await ctx.send(embed=embed)

    @commands.command()
    async def help(self,ctx: commands.Context, command_name: str | None = None):
        if command_name is None:
            embed = discord.Embed(
                title="🤖 Bot Help Menu",
                description=f"Use `{ctx.clean_prefix}help <command>` for more details.\n\nHere are all available commands:",
                color=discord.Color.blurple(),
            )
            if ctx.author.avatar:
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
            if ctx.bot.user and ctx.bot.user.avatar:
                embed.set_thumbnail(url=ctx.bot.user.avatar.url)

            embed.add_field(
                name="🧩 Utility",
                value=(
                    "`help` → Shows this help menu\n"
                    "`ping` → Check bot latency\n"
                    "`hello` → Say hello to the bot\n"
                    "`info` → Show bot/server info"
                ),
                inline=False
            )

            embed.add_field(
                name="🎓 Academic",
                value=(
                    "**Class Schedule:**\n"
                    "`addclass` → Open a menu to add a new class\n"
                    "`myschedule` → Show your class schedule\n"
                    "`delclass <subject>` → Delete a class by name\n"
                    "**Homework:**\n"
                    "`addhw` → Open a form to add homework\n"
                    "`hw` → Show all your pending homework\n"
                    "`delhw` → Delete homework by name"
                ),
                inline=False
            )

            embed.add_field(
                name="🛡️ Moderation (Mods Only)",
                value=(
                    "**Roles:**\n"
                    "`createrole` → Create a new role\n"
                    "`deleterole` → Remove a role by name\n"
                    "`addrole` → Add role to mentioned users\n"
                    "**Restaurant List:**\n"
                    "`basr <name>` → Add a **standard** restaurant\n"
                    "`bassr <name>` → Add a **special** restaurant\n"
                    "`bdrand <name>` → Delete a restaurant by name"
                ),
                inline=False,
            )

            embed.add_field(
                name="🎉 Fun & Games",
                value=(
                    "`brick [n]` → Send 1-10 random custom emojis\n"
                    "`bxdd` → Send a random XD response\n"
                    "`bsr` → Pick a random **standard** restaurant\n"
                    "`bssr` → Pick a random **special** restaurant\n"
                    "`bls` → List all restaurants"
                ),
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            return await ctx.send(embed=embed)

        cmd = self.bot.get_command(command_name)

        # Specific command case
        if cmd is None:
            return await ctx.send(f"❌ a command name {command_name} is not found.")

        embed = discord.Embed(
            title=f"❓ Help: {ctx.clean_prefix}{cmd.qualified_name}",
            color=discord.Color.blurple(),
        )

        if ctx.author.avatar:
            embed.set_author(
                name=ctx.author.display_name, icon_url=ctx.author.avatar.url
            )

        # Description
        desc = cmd.help or "No description has been set for this command yet."
        embed.add_field(name="Description", value=desc, inline=False)

        # Usage line
        usage = f"{ctx.clean_prefix}{cmd.qualified_name} {cmd.signature}".strip()
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)

        # Aliases
        if cmd.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in cmd.aliases),
                inline=False,
            )

        embed.set_footer(text=f"Requested by {ctx.author.name}")
        await ctx.send(embed=embed)

async def setup(bot : commands.Bot):
    await bot.add_cog(Info(bot))
