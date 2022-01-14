"""
Dredd Support, discord bot
Copyright (C) 2022 Moksej
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord

from discord.ext import commands


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="general-mute", aliases=['generalmute', 'genmute', 'gmute'])
    @commands.guild_only()
    @commands.has_role(679647636479148050)
    async def general_mute(self, ctx, users: commands.Greedy[discord.Member], *, reason: str):
        """ General mute multiple members permanently """

        if len(users) == 0:
            raise commands.MissingRequiredArgument(self.general_mute.params["users"])

        if len(reason) >= 450:
            return await ctx.send("Reason too long!")

        mute_role = ctx.guild.get_role(873189891519967284)
        modlogs = ctx.guild.get_channel(827971859667746838)
        muted = 0
        muted_list = []
        for user in users:
            if mute_role in user.roles or ctx.author.top_role.position < user.top_role.position or user.bot:
                continue
            await user.add_roles(mute_role, reason=f"[Staff: {ctx.author} - {ctx.author.id}] - {reason}")
            muted_list.append(f"{user.mention} ({user.id})\n")
            muted += 1

        e = discord.Embed(color=14301754, title=f"General muted {muted} members")
        members = ''.join(muted_list[:30]) + f"\n(+{muted - 30} more)"
        e.description = f"**Staff:** {ctx.author} ({ctx.author.id})\n**Reason:** {reason}\n**Members:**\n{members}"
        await modlogs.send(embed=e)
        await ctx.send(f"General muted {muted} members")

    @commands.command(name="voice-mute", aliases=['voicemute', 'vcmute'])
    @commands.guild_only()
    @commands.has_role(679647636479148050)
    async def voice_mute(self, ctx, users: commands.Greedy[discord.Member], *, reason: str):
        """ Voice mute multiple members permanently """

        if len(users) == 0:
            raise commands.MissingRequiredArgument(self.general_mute.params["users"])

        if len(reason) >= 450:
            return await ctx.send("Reason too long!")

        mute_role = ctx.guild.get_role(873198321580245032)
        modlogs = ctx.guild.get_channel(827971859667746838)
        muted = 0
        muted_list = []
        for user in users:
            if mute_role in user.roles or ctx.author.top_role.position < user.top_role.position or user.bot:
                continue
            await user.add_roles(mute_role, reason=f"[Staff: {ctx.author} - {ctx.author.id}] - {reason}")
            muted_list.append(f"{user.mention} ({user.id})\n")
            muted += 1

        e = discord.Embed(color=14301754, title=f"Voice muted {muted} members")
        members = ''.join(muted_list[:30]) + f"\n(+{muted - 30} more)"
        e.description = f"**Staff:** {ctx.author} ({ctx.author.id})\n**Reason:** {reason}\n**Members:**\n{members}"
        await modlogs.send(embed=e)
        await ctx.send(f"Voice muted {muted} members")


def setup(bot):
    bot.add_cog(Mod(bot))
