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

    return user


def button_children(self, display_support: bool = True):
    if not display_support:
        self.remove_item(self.children[0])
    self.remove_item(self.children[1])
    return self.children
