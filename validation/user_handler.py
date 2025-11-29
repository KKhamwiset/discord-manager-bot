import discord


import discord


async def resolve_members(ctx, raw_params: discord.Member | str):
    
    original_params = raw_params
    user_params = list(filter(lambda x: isinstance(x, discord.Member), original_params))
    string_params = list(filter(lambda x: isinstance(x, str), original_params))
    mentioned_members = list(ctx.message.mentions)

    name_map = {}
    for m in ctx.guild.members:
        normalized_name = m.name.lower()
        normalized_display = m.display_name.lower()
        name_map[normalized_name] = m
        name_map[normalized_display] = m

    if "@here" not in string_params:
        mentioned_members += [m for m in user_params if m not in mentioned_members]
        for query in string_params:
            q = query.lower()
            matches = [name for name in name_map.keys() if name.startswith(q)]

            for match in matches:
                m = name_map[match]
                if m not in mentioned_members and not m.bot:
                    mentioned_members.append(m)

    else:
        if isinstance(ctx.channel, discord.Thread):
            members = await ctx.channel.fetch_members()
            for partial in members:
                m = discord.utils.get(ctx.guild.members, id=partial.id)
                if m and not m.bot and m not in mentioned_members:
                    mentioned_members.append(m)
        else:
            await ctx.send("`@here` cannot be used here")
            return None

    return mentioned_members