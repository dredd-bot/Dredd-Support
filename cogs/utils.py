"""
Dredd Support, discord bot
Copyright (C) 2020 Moksej
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
from datetime import datetime
from utils.btime import FutureTime


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id != 671078170874740756:
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        if payload.message_id == 772461778470830110:
            if str(payload.emoji) in self.bot.config.ROLES:
                role = guild.get_role(self.bot.config.ROLES[str(payload.emoji)])
                await user.add_roles(role) 

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id != 671078170874740756:
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        if payload.message_id == 772461778470830110:
            if str(payload.emoji) in self.bot.config.ROLES:
                role = guild.get_role(self.bot.config.ROLES[str(payload.emoji)])
                await user.remove_roles(role)

    @commands.command(brief='Privacy policy', aliases=['pp', 'policy', 'privacypolicy'])
    async def privacy(self, ctx):
        e = discord.Embed(color=discord.Color.blurple(), title=f"{self.bot.user} Privacy Policy's")
        e.add_field(name='What data is being stored?', value="No data of you is being stored as of now", inline=False)
        e.add_field(name='What should I do if I have any concerns?', value=f"You can shoot a direct message to **{ctx.guild.owner}**, open a support ticket at <#783445230502019142> or email us at `support@dredd-bot.xyz`")
        await ctx.send(embed=e)
    
    @commands.command(name='time', brief='Displays Moksej\'s time')
    async def time(self, ctx):
        get_time = FutureTime('1h')
        time = get_time.dt
        await ctx.send(f"Current <@345457928972533773>'s time is: {time.strftime('%H:%M')} CET (Central European Time)", allowed_mentions=discord.AllowedMentions(users=False))

def setup(bot):
    bot.add_cog(Utils(bot))
