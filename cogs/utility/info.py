import discord , os 
from discord.ext import commands
from discord import app_commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

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

            # --- General / Fun ---
            embed.add_field(
                name="🧩 General & Fun",
                value=(
                    "`help` • `info` • `ping` • `hello`\n"
                    "`rick [n]` → Send random emoji (1-10)\n"
                    "`xdd` → Send random funny response"
                ),
                inline=False
            )

            # --- Academic ---
            embed.add_field(
                name="🎓 Academic (Schedule & HW)",
                value=(
                    "`addclass` → Add class to schedule\n"
                    "`editclass` → Edit class info\n"
                    "`myschedule` → View schedule\n"
                    "`delclass` → Delete class\n"
                    "`addhw` → Add homework\n"
                    "`hw` → View pending homework\n"
                    "`delhw` → Delete homework"
                ),
                inline=False
            )

            # --- Randomizer ---
            embed.add_field(
                name="🍱 Restaurant Randomizer",
                value=(
                    "`nrand` (sr) → Random Standard\n"
                    "`srand` (ssr) → Random Special\n"
                    "`lrand` (ls) → List all\n"
                    "`arand` / `asrand` → Add Std/Special (Mod)\n"
                    "`drand` → Delete restaurant (Mod)"
                ),
                inline=False
            )
            
            # --- Moderation ---
            embed.add_field(
                name="🛡️ Role Management (Mod Only)",
                value=(
                    "`createrole` (cr) → Create role\n"
                    "`editrole` (er) → Edit role name/color\n"
                    "`deleterole` (dr) → Delete role\n"
                    "`addrole` (ar) → Give role to user\n"
                    "`removerole` (rr) → Remove role from user\n"
                    "`listrole` (lr) [user/role] → List roles"
                ),
                inline=False,
            )

            # --- Channel Config ---
            embed.add_field(
                name="⚙️ Channel Config (Mod Only)",
                value=(
                    "`setbotchannel` → Set allowed commands\n"
                    "`disablebotchannel` → Disable bot in channel\n"
                    "`listbotchannels` → View config"
                ),
                inline=False,
            )

            embed.set_footer(text=f"Requested by {ctx.author.name}")
            return await ctx.send(embed=embed)

        # --- Specific Command Help ---
        cmd = self.bot.get_command(command_name)

        if cmd is None:
            return await ctx.send(f"❌ Command `{command_name}` not found.")

        embed = discord.Embed(
            title=f"❓ Help: {ctx.clean_prefix}{cmd.qualified_name}",
            description=cmd.help or "No description provided.",
            color=discord.Color.blurple(),
        )

        # Usage
        usage = f"{ctx.clean_prefix}{cmd.qualified_name} {cmd.signature}".strip()
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)

        # Aliases
        if cmd.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in cmd.aliases),
                inline=False,
            )

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))