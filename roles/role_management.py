import discord
from discord.ext import commands
import random

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def role_validate(self, roles):
        if not any("Moderator" in i.name for i in roles):
            return False
        return True

    @commands.command()
    async def crole(self, ctx, role_name: str, color: str = None):
        validate = self.role_validate(ctx.author.roles)
        if not validate:
            await ctx.send("❌ You need to be a bot admin to use this command.")
            return
        guild = ctx.guild
        existing_role = discord.utils.get(guild.roles, name=role_name)

        if existing_role:
            await ctx.send(f"⚠️ Role `{existing_role.name}` already exists.")
            return

        # 🎨 choose color
        if color:
            # try to convert hex -> int
            try:
                color_value = discord.Color(int(color.lstrip('#'), 16))
            except ValueError:
                await ctx.send("❌ Invalid color format! Use a hex code like `#FF0000`.")
                return
        else:
            # random color
            color_value = discord.Color(random.randint(0x000000, 0xFFFFFF))

        # create role
        new_role = await guild.create_role(name=role_name, color=color_value)
        await ctx.send(f"✅ Role `{new_role.name}` created with color `{str(new_role.color)}`.")