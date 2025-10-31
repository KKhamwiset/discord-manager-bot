import discord
from discord.ext import commands

class Info(commands.Cog):
    def __init__(self,bot):
        self.bot = bot 

    @commands.command()
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
    async def help(self,ctx: commands.Context):
        embed = discord.Embed(
            title="🤖 Bot Help Menu",
            description="Here are all available commands!",
            color=discord.Color.blurple()
        )
        if ctx.author.avatar:
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        if ctx.bot.user and ctx.bot.user.avatar:
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)

        embed.add_field(
            name="🧩 General",
            value=(
                "`bping` → Check bot latency\n"
                "`bhello` → Say hello to the bot\n"
                "`binfo` → Show bot/server info\n"
                "`bbrick [n]` → Send random brick emojis (1–10)"
            ),
            inline=False
        )
        embed.add_field(
            name="🛠️ Role Management",
            value=(
                "`bcrole <role_name> [#color]` → Create a new role (random color if none)\n"
                "`brrole <role_name>` → Remove a role by name\n"
                "`barole <role_name> @user1 @user2 ...` → Add role to mentioned users"
            ),
            inline=False
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        await ctx.send(embed=embed)

async def setup(bot : commands.Bot):
    await bot.add_cog(Info(bot))

