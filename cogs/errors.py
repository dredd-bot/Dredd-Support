"""
Dredd Support, discord bot
Copyright (C) 2021 Moksej
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
import json
import traceback
import asyncio

from discord.ext import commands, tasks
from discord.utils import escape_markdown
from datetime import datetime, timezone

from utils import btime
from utils.default import bot_acknowledgements


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def sync_member_roles(self, member):
        channel = self.bot.get_channel(675742172015755274)
        try:
            badges = await self.bot.db.fetchval("SELECT * FROM badges WHERE _id = $1", member.id)
            try:
                early = member.guild.get_role(679642623107137549)
                partner = member.guild.get_role(683288670467653739)
                booster = member.guild.get_role(686259869874913287)
                verified = member.guild.get_role(733817083330297959)
                bugs = member.guild.get_role(679643117510459432)
                sponsor = member.guild.get_role(779299456125763584)
                for badge in bot_acknowledgements(self.context, member, simple=True).split(' '):
                    if badge in ['<:es:686251890299633701>', '<:e_s:749334042805010452>']:
                        await member.add_roles(early)
                    elif badge == '<:p_:748833273383485440>':
                        await member.add_roles(partner)
                    elif badge == '<:n_:747399776231882812>':
                        await member.add_roles(booster)
                    elif badge in ['<:b2:706190136991416341>', '<:b1:691667204675993672>']:
                        await member.add_roles(bugs)
                    elif badge == '🌟':
                        await member.add_roles(sponsor)
            except KeyError:
                pass
            except Exception as error:
                tb = traceback.format_exception(type(error), error, error.__traceback__)
                tbe = "".join(tb) + ""
                e = discord.Embed(color=discord.Color.red(), title='Error Occured whilst trying to add a role to new member!')
                e.description = tbe
                await channel.send(embed=e, content=f"Failed to add roles for {member.mention} `({member.name} - {member.id})`")
        except Exception as e:
            await channel.send(f"Error occured when trying to add the role: {e}")

    async def process_blacklist(self, member):
        blacklist = await self.bot.db.fetch("SELECT issued, reason, liftable FROM blacklist WHERE _id = $1 AND type = 2", member.id)

        if blacklist:
            bl_role = member.guild.get_role(734537587116736597)
            for role in member.roles:
                await member.remove_roles(role)
            await member.add_roles(bl_role)

            if blacklist['liftable'] == 0:
                e = discord.Embed(color=14301754, title="Blacklist Appeal", timestamp=datetime.now(timezone.utc))
                e.description = (f"Hello {member.name},\nSince you are blacklisted you will not be gaining access to the rest of the server. "
                                 "However, you may appeal your blacklist, please provide a reason in here, stating, why you should be unblacklisted."
                                 "\n*If you leave your blacklist appeal will be immediately declined and you will be banned from this server and will only be able to appeal through mail `(support@dredd-bot.xyz)`.*\n"
                                 f"**Reason for your blacklist:** {blacklist['reason']}\n**Issued:** {btime.human_timedelta(blacklist['issued'])}")

                bot_admin = member.guild.get_role(674929900674875413)
                overwrites = {
                    member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    member.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    bot_admin: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                }
                category = member.guild.get_channel(830861235955433512)
                channel = await member.guild.create_text_channel(name=f'blacklist-{member.id}', overwrites=overwrites, category=category, reason="Blacklisted and is able to appeal")

                await channel.send(embed=e, content=member.mention, allowed_mentions=discord.AllowedMentions(users=True))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exc):

        if hasattr(ctx.command, 'on_error'):
            return

        elif isinstance(exc, commands.CommandNotFound):
            return
        elif isinstance(exc, commands.CommandInvokeError):
            ctx.command.reset_cooldown(ctx)
            exc = exc.original
        elif isinstance(exc, commands.MissingRole):
            role = ctx.guild.get_role(exc.missing_role)
            return await ctx.send(f"You need the following role to execute this command - {role.mention}.")
        elif isinstance(exc, commands.MissingRequiredArgument):
            return await ctx.send(f"Argument **{exc.param.name}** is missing")
        elif isinstance(exc, commands.CheckFailure):
            return
        elif isinstance(exc, commands.TooManyArguments):
            if isinstance(ctx.command, commands.Group):
                return
        else:
            channel = self.bot.get_channel(675742172015755274)
            e = discord.Embed(color=discord.Color.red(), title='Error Occured!')
            e.description = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            e.add_field(name="Information:", value=f"**Short error:** {exc}\n**Command:** {ctx.command.qualified_name}")
            await channel.send(embed=e)

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
                    message = f"\n<:offline:686955649032388623> The bot is now offline! This may be due to a restart, or it could be due to an outage! `[{datetime.utcnow().strftime('%H:%M')} UTC]`"
                    moksej_mention = f"{self.bot.get_user(345457928972533773).mention}"
                    await channel.send(message)
                    await channel.send(moksej_mention, delete_after=1)

    @commands.Cog.listener()
    async def on_ready(self):
        m = "Logged in as:"
        m += "\nName: {0} ({0.id})".format(self.bot.user)
        m += f"\nTime taken to boot: {btime.human_timedelta(self.bot.uptime.replace(tzinfo=None), suffix=None)}"
        print(m)
        await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching,
                                          name="s?help"))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != 671078170874740756:
            return
        elif member.guild.id == 671078170874740756:
            if member.bot:
                return
            await self.sync_member_roles(member=member)
            await self.process_blacklist(member=member)
        else:
            return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != 671078170874740756:
            return
        elif member.guild.id == 671078170874740756:
            channel = discord.utils.find(lambda r: r.name == f"blacklist-{member.id}", member.guild.channels)
            if member.bot:
                return
            elif channel:
                await channel.send("They left. Banning them from the server.")
                await member.guild.ban(member, reason=f"Left without getting blacklist appeal sorted {datetime.utcnow()}")

    @commands.Cog.listener('on_member_update')
    async def del_status_logging(self, before, after):  # this event is for DEL server.
        await self.bot.wait_until_ready()

        if before.guild.id != 632908146305925129:
            return

        if not before.bot:
            return

        log_channel = self.bot.get_channel(786658498175828058)
        if before.status != after.status:
            time = datetime.utcnow()
            if after.status == discord.Status.offline:
                await log_channel.send(f"<:offline:793508541519757352> {after.mention} - {after.name} ({after.id}) is offline! - {time.strftime('%H:%M %D')} UTC")
            elif before.status == discord.Status.offline and after.status != discord.Status.offline:
                await log_channel.send(f"<:online:772459553450491925> {after.mention} - {after.name} ({after.id}) is online! - {time.strftime('%H:%M %D')} UTC")


def setup(bot):
    bot.add_cog(Errors(bot))
