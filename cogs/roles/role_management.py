import discord
from discord.ext import commands
import random

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def role_validate(self, roles : list[discord.Role]):
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

        if color:
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
        
    @commands.command()
    async def rrole(self,ctx, role_name: str):
        validate = self.role_validate(ctx.author.roles)
        if not validate:
            await ctx.send("❌ You need to be a bot admin to use this command.")
            return
        guild = ctx.guild
        existing_role = discord.utils.get(guild.roles, name=role_name)

        if not existing_role:
            await ctx.send(f"⚠️ Role `{role_name}` does not exist.")
            return
        await existing_role.delete()
        await ctx.send(f"✅ Deleted role `{role_name}`")

    @commands.command()
    async def arole(self,ctx, role_name: str):
        validate = self.role_validate(ctx.author.roles)
        if not validate:
            await ctx.send("❌ You need to be a bot admin to use this command.")
            return
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=role_name)

        if not role:
            await ctx.send(f"⚠️ Role `{role_name}` does not exist.")
            return

        mentioned_members = ctx.message.mentions

        if not mentioned_members:
            await ctx.send("❌ You need to mention at least one user.")
            return

        for member in mentioned_members:
            await member.add_roles(role)
            await ctx.send(f"✅ Added role `{role.name}` to {member.mention}")

        await ctx.send(f"🎉 Done! Role `{role.name}` added to all mentioned users.")
        
async def setup(bot : commands.Bot):
    await bot.add_cog(RoleManagement(bot))