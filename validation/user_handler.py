import discord


async def resolve_members(ctx, raw_params : discord.Member | str):
    original_params = raw_params
    user = list(filter(lambda x: isinstance(x, discord.Member), original_params))
    any_string = list(filter(lambda x: isinstance(x, str), original_params))
    mentioned_members = list(ctx.message.mentions)

    if "@here" not in any_string:
        mentioned_members += [i for i in user if i not in mentioned_members]
        if any_string:
            for name in any_string:
                name = name.lower() if name.isalpha() else name
                username = [i.name.lower() for i in ctx.guild.members]
                display_name = [i.display_name.lower() if i.display_name.isalpha() else i.display_name for i in ctx.guild.members]
                username.extend(display_name)
                all_name = username
                filter_member = list(filter(lambda i: i.startswith(name), all_name))
                for member_name in filter_member:
                    member = (
                        discord.utils.get(ctx.guild.members, name=member_name) or
                        discord.utils.get(ctx.guild.members, display_name=member_name)
                    )
                    if member and member not in mentioned_members and not member.bot:
                        mentioned_members += [member]
        else:
            pass
    else:
        if isinstance(ctx.channel, discord.Thread):
            member = await ctx.channel.fetch_members()
            member = [
                discord.utils.get(ctx.guild.members, id=i.id)
                for i in member
                if discord.utils.get(ctx.guild.members, id=i.id) not in mentioned_members
                and not discord.utils.get(ctx.guild.members, id=i.id).bot
            ]
            mentioned_members += member
        else:
            await ctx.send("`@here` cannot be use here")
            return None

    return mentioned_members

