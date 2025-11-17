import discord
from discord.ext import commands


def role_validation():
    async def check_permissions(wrapped_ctx: commands.Context):
        author_roles = wrapped_ctx.author.roles
        member = [i for i in list(wrapped_ctx.args)if isinstance(i, discord.Member)]

        if not any("Moderator" in r.name for r in author_roles):
            await wrapped_ctx.send(
                embed=discord.Embed(
                    title="❌ Permission Denied",
                    description="You must have Moderator role to use this.",
                    color=discord.Color.red()
                )
            )
            return False
        requester_top = max(author_roles, key=lambda r: r.position)

        members = list(wrapped_ctx.message.mentions)
        members += [i for i in member if i not in members]
        if members:
            for m in members:
                target_top = max(m.roles, key=lambda r: r.position)
                if requester_top.position <= target_top.position:
                    await wrapped_ctx.send(
                        embed=discord.Embed(
                            title="❌ Permission Denied",
                            description=f"You cannot modify roles of user `{m.display_name}` with equal/higher roles.",
                            color=discord.Color.red()
                        )
                    )
                    return False

        return True
    return commands.check(check_permissions)
