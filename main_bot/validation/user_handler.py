import discord
from typing import Optional, Union, List

async def resolve_members(ctx, raw_params: Union[List[str], str]) -> Optional[List[discord.Member]]:
    if not isinstance(raw_params, (list, tuple)):
        raw_params = [raw_params]
        
    user_params = [x for x in raw_params if isinstance(x, discord.Member)]
    string_params = [x for x in raw_params if isinstance(x, str)]
    mentioned_members = list(ctx.message.mentions)

    if "@here" not in string_params:
        mentioned_members += [m for m in user_params if m not in mentioned_members]
        
        # Lowercase queries once
        queries = [q.lower() for q in string_params]
        
        for m in ctx.guild.members:
            if m.bot or m in mentioned_members:
                continue
                
            name_lower = m.name.lower()
            display_lower = m.display_name.lower()
            
            for q in queries:
                if name_lower.startswith(q) or display_lower.startswith(q):
                    mentioned_members.append(m)
                    break

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