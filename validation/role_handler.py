import discord
from discord.ext import commands


def role_validation():
    async def check_permissions(wrapped_ctx: commands.Context):
        member = [i for i in list(wrapped_ctx.args)if isinstance(i, discord.Member)]

        if not any("Moderator" in r.name for r in wrapped_ctx.author.roles):
            await wrapped_ctx.send(
                embed=discord.Embed(
                    title="❌ Permission Denied",
                    description="You must have Moderator role to use this.",
                    color=discord.Color.red()
                )
            )
            return False
        requester_top = wrapped_ctx.author.top_role

        members = list(wrapped_ctx.message.mentions)
        members += [i for i in member if i not in members]
        if members:
            for m in members:
                target_top = m.top_role
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

async def resolve_roles(ctx, raw_params: list[str]) -> list[discord.Role]:
    if not isinstance(raw_params, (list, tuple)):
        raw_params = [raw_params]
    original_params = raw_params
    role_params = list(filter(lambda x: isinstance(x, discord.Role), original_params))
    string_params = list(filter(lambda x: isinstance(x, str), original_params))
    mentioned_roles = list(ctx.message.role_mentions)

    name_map = {}
    for r in ctx.guild.roles:
        normalized_name = r.name.lower()
        name_map[normalized_name] = r

    mentioned_roles += [r for r in role_params if r not in mentioned_roles]
    for query in string_params:
        q = query.lower()
        matches = [name for name in name_map.keys() if name.startswith(q)]
        for match in matches:
            r = name_map[match]
            if r not in mentioned_roles:
                mentioned_roles.append(r)

    return mentioned_roles