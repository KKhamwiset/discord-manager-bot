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
        """Shows this help message"""
        embed = discord.Embed(
            title="🤖 Bot Help Menu",
            description=f"My prefixes are **`b`** or **`t`**. Here are all my commands!",
            color=discord.Color.blurple()
        )
        if ctx.author.avatar:
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        if ctx.bot.user and ctx.bot.user.avatar:
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)

        embed.add_field(
            name="🧩 Utility",
            value=(
                "`bhelp` → Shows this help menu\n"
                "`bping` → Check bot latency\n"
                "`bhello` → Say hello to the bot\n"
                "`binfo` → Show bot/server info"
            ),
            inline=False
        )

        embed.add_field(
            name="🎓 Academic",
            value=(
                "**Class Schedule:**\n"
                "`baddclass` → Open a menu to add a new class\n"
                "`bmyschedule` → Show your class schedule\n"
                "`bdelclass <subject>` → Delete a class by name\n"
                "**Homework:**\n"
                "`baddhw` → Open a form to add homework\n"
                "`bhw` → Show all your pending homework\n"
                "`bdelhw <name>` → Delete homework by name"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Moderation (Mods Only)",
            value=(
                "**Roles:**\n"
                "`bcrole <name> [#color]` → Create a new role\n"
                "`brrole <name>` → Remove a role by name\n"
                "`barole <name> @user...` → Add role to mentioned users\n"
                "**Restaurant List:**\n"
                "`basr <name>` → Add a **standard** restaurant\n"
                "`bassr <name>` → Add a **special** restaurant\n"
                "`bdrand <name>` → Delete a restaurant by name"
            ),
            inline=False
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
        await ctx.send(embed=embed)

async def setup(bot : commands.Bot):
    await bot.add_cog(Info(bot))