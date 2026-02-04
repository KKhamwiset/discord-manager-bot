import discord
from discord.ext import commands
from validation import resolve_members, resolve_roles
import random
import validation

class RoleManagement(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="createrole", aliases=["cr", "makerole"], help="Create a role")
    @validation.role()
    async def createRole(self, ctx, role_name: str, color: str = None):
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
    @validation.role()
    async def removeRole(self,ctx, role_name: discord.Role | str):
        guild = ctx.guild
        if isinstance(role_name, discord.Role):
            role_name = role_name.name
        else:
            role_filter = await resolve_roles(ctx, [role_name])
            if role_filter:
                role_name = role_filter[0].name

        existing_role = discord.utils.get(guild.roles, name=role_name)

        if not existing_role:
            await ctx.send(f"⚠️ Role `{role_name}` does not exist.")
            return
        await existing_role.delete()
        await ctx.send(f"✅ Deleted role `{role_name}`")

    @commands.command(name="listrole",aliases=["lr","roles"], help="List all roles in the server / List user roles")
    async def listRoles(self,ctx, params : discord.Member | discord.guild.Role | str = None):
        guild = ctx.guild
        user = None
        role = None
        if isinstance(params, discord.Member):
            user = params
        elif isinstance(params, discord.Role):
            role = params
        else:
            if params is not None:
                role_filter = await resolve_roles(ctx, [params])
                if role_filter:
                    role = role_filter[0]
                user_filter = await resolve_members(ctx, [params])
                if user_filter:
                    user = user_filter[0] 
        if user is not None:
            user_roles = [role.name for role in user.roles if role.name != "@everyone"][::-1]
            if not user_roles:
                await ctx.send(f"⚠️ `{user.display_name}` has no roles.")
                return

            roles_text = "\n".join([f" - `{r}`" for r in user_roles])
            embed = discord.Embed(title=f"Roles for {user.display_name}", description=roles_text, color=user.top_role.color if user.top_role else discord.Color.dark_gold(), timestamp=ctx.message.created_at)
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed.add_field(name="Total Roles", value=str(len(user_roles)), inline=False)
            embed.add_field(name="Highest Role", value=f"- **{user.top_role.name}**" if user.top_role else "@everyone", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
            return

        if role is not None:
            role_members = sorted(role.members, key=lambda m: m.top_role.position, reverse=True)
            role_members_names = [member.display_name for member in role_members]
            
            if not role_members_names:
                await ctx.send(f"⚠️ Role `{role.name}` has no members.")
                return
            
            members_text = "\n".join([f"• {m}" for m in role_members_names[:50]]) 
            if len(role_members_names) > 50:
                members_text += f"\n...and {len(role_members_names) - 50} more"

            embed = discord.Embed(title=f"Members with role: {role.name}", description=members_text, color=role.color, timestamp=ctx.message.created_at)
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            embed.add_field(name="Total Members", value=str(len(role_members)), inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
            return
        
        roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
        role_names = [role.name for role in roles if role.name != "@everyone"]
        if not role_names:
            await ctx.send("⚠️ No roles found in this server.")
            return
        
        role_list = "\n".join([f" - `{r}`" for r in role_names[:50]])
        if len(role_names) > 50:
            role_list += f"\n...and {len(role_names) - 50} more"

        embed = discord.Embed(title=f"Roles in {guild.name}", description=role_list, color=discord.Color.dark_gold(), timestamp=ctx.message.created_at)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Total Roles", value=str(len(role_names)), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="removerole",aliases=["removerolefromuser","rr"], help="Remove a role from users")
    @validation.role()
    async def removeRoleFromUser(self,ctx, role_name: discord.Role | str ,*user: discord.Member | str):
        mentioned_members = await resolve_members(ctx, user)
        guild = ctx.guild
        if isinstance(role_name, discord.Role):
            role = role_name
        else:
            role_filter = await resolve_roles(ctx, [role_name])
            if role_filter:
                role_name = role_filter[0].name
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
    async def addRole(self,ctx, role_name: discord.Role | str,*user: discord.Member | str):
        guild = ctx.guild
        if isinstance(role_name, discord.Role):
            role = role_name
        else:
            role_filter = await resolve_roles(ctx, [role_name])
            if role_filter:
                role_name = role_filter[0].name
            role = discord.utils.get(guild.roles, name=role_name)

        if not role:
            await ctx.send(f"⚠️ Role `{role_name}` does not exist.")
            return
        
        mentioned_members = await resolve_members(ctx, user)
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
