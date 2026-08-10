from collections.abc import Iterable

import discord
from discord.ext import commands


GUILD_ONLY_MESSAGE = "❌ This command can only be used in a server."


async def _is_application_owner(ctx: commands.Context) -> bool:
    try:
        return await ctx.bot.is_owner(ctx.author)
    except Exception:
        return False


async def _send_permission_denied(ctx: commands.Context, permission_label: str) -> None:
    await ctx.send(
        embed=discord.Embed(
            title="❌ Permission Denied",
            description=f"You need the `{permission_label}` server permission to use this command.",
            color=discord.Color.red(),
        )
    )


def guild_only():
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is not None:
            return True
        await ctx.send(GUILD_ONLY_MESSAGE)
        return False

    return commands.check(predicate)


def native_permission(permission_name: str, permission_label: str | None = None):
    label = permission_label or permission_name.replace("_", " ").title()

    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            await ctx.send(GUILD_ONLY_MESSAGE)
            return False

        if await _is_application_owner(ctx):
            return True

        permissions = getattr(ctx.author, "guild_permissions", None)
        if permissions is not None and (
            getattr(permissions, "administrator", False)
            or getattr(permissions, permission_name, False)
        ):
            return True

        await _send_permission_denied(ctx, label)
        return False

    return commands.check(predicate)


def manage_guild():
    return native_permission("manage_guild", "Manage Server")


def manage_roles():
    return native_permission("manage_roles", "Manage Roles")


def manage_threads():
    return native_permission("manage_threads", "Manage Threads")


def owner_only():
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            await ctx.send(GUILD_ONLY_MESSAGE)
            return False
        if await _is_application_owner(ctx):
            return True
        await ctx.send(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="Only the bot owner can use this command.",
                color=discord.Color.red(),
            )
        )
        return False

    return commands.check(predicate)


def role_mutation_error(
    guild: discord.Guild,
    actor: discord.Member,
    bot_member: discord.Member | None,
    role: discord.Role,
    target_members: Iterable[discord.Member] = (),
) -> str | None:
    """Return a user-facing reason when a role mutation is unsafe.

    Application ownership is intentionally irrelevant here. Discord hierarchy is
    bypassed only by the Discord guild owner, while the bot must always be above
    every role and member it will mutate.
    """
    targets = tuple(target_members)

    if role.is_default():
        return "The default `@everyone` role cannot be modified."
    if role.managed:
        return f"Role `{role.name}` is managed by Discord or an integration."

    actor_is_guild_owner = actor.id == guild.owner_id
    if not actor_is_guild_owner:
        if actor.top_role.position <= role.position:
            return f"Your highest role must be above `{role.name}`."
        for member in targets:
            if actor.top_role.position <= member.top_role.position:
                return f"Your highest role must be above `{member.display_name}`."

    if bot_member is None:
        return "The bot member could not be resolved for this server."
    if bot_member.top_role.position <= role.position:
        return f"The bot's highest role must be above `{role.name}`."
    for member in targets:
        if bot_member.top_role.position <= member.top_role.position:
            return f"The bot's highest role must be above `{member.display_name}`."

    return None


# Kept for compatibility with extensions outside this authorization migration.
def role_validation():
    return manage_guild()


async def resolve_roles(ctx, raw_params: list[str]) -> list[discord.Role]:
    if not isinstance(raw_params, (list, tuple)):
        raw_params = [raw_params]
    original_params = raw_params
    role_params = list(filter(lambda x: isinstance(x, discord.Role), original_params))
    string_params = list(filter(lambda x: isinstance(x, str), original_params))
    mentioned_roles = list(ctx.message.role_mentions)

    name_map = {}
    for role in ctx.guild.roles:
        normalized_name = role.name.lower()
        name_map[normalized_name] = role

    mentioned_roles += [role for role in role_params if role not in mentioned_roles]
    for query in string_params:
        q = query.lower()
        matches = [name for name in name_map.keys() if name.startswith(q)]
        for match in matches:
            role = name_map[match]
            if role not in mentioned_roles:
                mentioned_roles.append(role)

    return mentioned_roles
