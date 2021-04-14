import discord


async def find_user(ctx, user):
    user = user or ctx.author
    if isinstance(user, discord.User):
        pass
    elif isinstance(user, str):
        if not user.isdigit():
            return None
        try:
            user = await ctx.bot.fetch_user(user)
        except Exception:
            return None

    return 
