import discord
from discord.ext import commands
import random

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def role_validate(self, roles : list[discord.Role], * ,members: list[discord.Member] = None) -> bool:

        if not any("Moderator" in i.name for i in roles):
            return False
        
        requested_role = max(roles, key=lambda r: r.position)

        if members is not None:
            for member in members:
                target_role = max(member.roles, key=lambda r: r.position)
                if requested_role.position <= target_role.position:
                    return False
    
        return True

    @commands.command(name="createrole", aliases=["cr", "makerole"], help="Create a role")
    async def createRole(self, ctx, role_name: str, color: str = None):
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

    @commands.command(name="deleterole",aliases=["dr","delrole"], help="Delete a role")
    async def removeRole(self,ctx, role_name: str):
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

    @commands.command(name="listrole",aliases=["lr","roles"], help="List all roles in the server / List user roles")
    async def listRoles(self,ctx, user: discord.Member = None):
        guild = ctx.guild
        if user is not None:
            user_roles = [role.name for role in user.roles if role.name != "@everyone"]

            if not user_roles:
                await ctx.send(f"⚠️ `{user.display_name}` has no roles.")
                return

            roles_text = "\n".join(user_roles)
            await ctx.send(f"📜 Roles for `{user.display_name}`:\n{roles_text}")
            return
        
        roles = sorted(guild.roles,key=lambda r: r.position, reverse=True)
        role_names = [role.name for role in roles if role.name != "@everyone"]
        if not role_names:
            await ctx.send("⚠️ No roles found in this server.")
            return
        role_list = "\n".join(role_names)
        await ctx.send(f"Order 📜 Roles in this server:\n{role_list}")

    @commands.command(name="removerole",aliases=["removerolefromuser","rr"], help="Remove a role from users")
    async def removeRoleFromUser(self,ctx, role_name: str,*user: discord.Member):
        mentioned_members = list(ctx.message.mentions)
        mentioned_members += [i for i in user if i not in mentioned_members]
        print(mentioned_members)
        validate = self.role_validate(ctx.author.roles,members=mentioned_members)
        if not validate:
            await ctx.send("❌ You need to be a bot admin to use this command or modify roles of users with equal/higher roles.")
            return
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=role_name)

        if not role:
            await ctx.send(f"⚠️ Role `{role_name}` does not exist.")
            return
        if not mentioned_members:
            await ctx.send("❌ You need to mention at least one user.")
            return

        for member in mentioned_members:
            if member.roles and role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"✅ Role `{role.name}` removed from user `{member.display_name}`.")
            else:
                await ctx.send(f"⚠️ User `{member.display_name}` does not have the role `{role.name}`.")
                await ctx.send("⏭️ Skipping to the next user.")

        await ctx.send(f"🎉 Done! Role `{role.name}` removed from all mentioned users.")

    @commands.command(name="addrole", aliases=["arole", "ar"], help="Add a role to users")
    async def addRole(self,ctx, role_name: str,*user: discord.Member):
        mentioned_members = list(ctx.message.mentions)
        mentioned_members += [i for i in user if i not in mentioned_members]
        validate = self.role_validate(ctx.author.roles)
        if not validate:
            await ctx.send("❌ You need to be a bot admin to use this command.")
            return
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=role_name)

        if not role:
            await ctx.send(f"⚠️ Role `{role_name}` does not exist.")
            return
 
        if not mentioned_members:
            await ctx.send("❌ You need to mention at least one user.")
            return

        for member in mentioned_members:
            if member.roles and role in member.roles:
                await ctx.send(f"⚠️ User `{member.display_name}` already has the role `{role.name}`.")
                await ctx.send("⏭️ Skipping to the next user.")
                continue
            else:
                await member.add_roles(role)
                await ctx.send(f"✅ Role `{role.name}` added to user `{member.display_name}`.")

        await ctx.send(f"🎉 Done! Role `{role.name}` added to all mentioned users.")

async def setup(bot : commands.Bot):
    await bot.add_cog(RoleManagement(bot))
