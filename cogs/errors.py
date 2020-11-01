"""
Dredd, discord bot
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
import os
import datetime
import json
import traceback
import asyncio

from discord.ext import commands, tasks
from discord.utils import escape_markdown
from datetime import datetime

from utils import btime
from db import emotes


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def sync_member_roles(self, member):
        try:
            with open('D:/dredd/db/badges.json', 'r') as f:
                data = json.load(f)
            try:
                badges = data['Users'][f"{member.id}"]['Badges']
                early = member.guild.get_role(679642623107137549)
                partner = member.guild.get_role(683288670467653739)
                booster = member.guild.get_role(686259869874913287)
                verified = member.guild.get_role(733817083330297959)
                bugs = member.guild.get_role(679643117510459432)
                for badge in badges:
                    if badge == emotes.bot_early_supporter:
                        await member.add_roles(early)
                    elif badge == emotes.bot_partner:
                        await member.add_roles(partner)
                    elif badge == emotes.bot_booster:
                        await member.add_roles(booster)
                    elif badge == emotes.bot_verified:
                        await member.add_roles(verified)
                    elif badge == emotes.discord_bug1 or badge == emotes.discord_bug2:
                        await member.add_roles(bugs)
            except KeyError:
                pass
            except Exception as error:
                tb = traceback.format_exception(type(error), error, error.__traceback__) 
                tbe = "".join(tb) + ""
                print(tbe)
                pass
        except Exception as e:
            print(e)
            pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exc):

        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(exc, commands.CommandNotFound):
            return
        if isinstance(exc, commands.CommandInvokeError):
            ctx.command.reset_cooldown(ctx)
            exc = exc.original
        if isinstance(exc, commands.CheckFailure):
            return
        if isinstance(exc, commands.TooManyArguments):
            if isinstance(ctx.command, commands.Group):
                return
        
        print(exc)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Ready as {self.bot.user}!")
    
    @commands.Cog.listener('on_member_update')
    async def on_dredd_die(self, before, after):
        if before.id != 667117267405766696:
            return
        elif before.id == 667117267405766696:
            offline = discord.Status.offline
            if after.status == offline:
                await asyncio.sleep(120)
                if after.status == offline:
                    channel = self.bot.get_channel(686934726853787773)
                    guild = self.bot.get_guild(671078170874740756)
                    role = guild.get_role(741748857888571502)
                    message = f"\n<:offline:686955649032388623> The bot is now offline! This may be due to a restart, or it could be due to outage! `[{datetime.utcnow().strftime('%H:%M')} UTC]`"
                    moksej_mention = f"{self.bot.get_user(345457928972533773).mention}"
                    await channel.send(message)
                    await channel.send(moksej_mention, delete_after=1)

    @commands.Cog.listener()
    async def on_ready(self):
        m = "Logged in as:"
        m += "\nName: {0} ({0.id})".format(self.bot.user)
        m += f"\nTime taken to boot: {btime.human_timedelta(self.bot.uptime, suffix=None)}"
        print(m)
        await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching,
                                          name="s?help")
            )
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != 671078170874740756:
            return
        elif member.guild.id == 671078170874740756:
            if member.bot:
                return
            await self.sync_member_roles(member=member)
        else:
            return
        

def setup(bot):
    bot.add_cog(Errors(bot))
