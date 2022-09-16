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
import os
import json
import traceback
import asyncio

from discord.ext import commands, tasks
from discord.utils import escape_markdown
from datetime import datetime, timezone

from utils import btime, publicflags


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
#         self.update_channel_stats.start()

#     def cog_unload(self):
#         self.update_channel_stats.cancel()

    async def sync_member_roles(self, member):
        channel = self.bot.get_channel(675742172015755274)
        try:
            badges = await self.bot.db.fetchval("SELECT flags FROM badges WHERE _id = $1", member.id)
            if not badges:
                return
            try:
                early = member.guild.get_role(679642623107137549)
                partner = member.guild.get_role(683288670467653739)
                booster = member.guild.get_role(686259869874913287)
                verified = member.guild.get_role(733817083330297959)
                bugs = member.guild.get_role(679643117510459432)
                sponsor = member.guild.get_role(779299456125763584)
                flags = publicflags.BotFlags(badges)
                for badge in [*flags]:
                    if badge in ['early', 'early_supporter']:
                        await member.add_roles(early)
                    elif badge == 'bot_partner':
                        await member.add_roles(partner)
                    elif badge == 'donator':
                        await member.add_roles(booster)
                    elif badge in ['bug_hunter_lvl1', 'bug_hunter_lvl2']:
                        await member.add_roles(bugs)
                    elif badge == 'sponsor':
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
        await asyncio.sleep(5)
        blacklist = await self.bot.db.fetch("SELECT issued, reason, liftable FROM blacklist WHERE _id = $1 AND type = 2", member.id)

        if blacklist:
            bl_role = member.guild.get_role(734537587116736597)
            for role in member.roles:
                if role.name == '@everyone':
                    continue
                await member.remove_roles(role)
            await member.add_roles(bl_role)

            if blacklist[0]['liftable'] == 0:
                e = discord.Embed(color=14301754, title="Blacklist Appeal", timestamp=datetime.now(timezone.utc))
                e.description = (f"Hello {member.name},\nSince you are blacklisted you will not be gaining access to the rest of the server. "
                                 "However, you may appeal your blacklist, please provide a reason in here, stating, why you should be unblacklisted."
                                 "\n*If you leave your blacklist appeal will be immediately declined and you will be banned from this server and will only be able to appeal through mail `(support@dreddbot.xyz)`.*\n"
                                 f"**Reason for your blacklist:** {blacklist[0]['reason']}\n**Issued:** {btime.human_timedelta(blacklist[0]['issued'])}")

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
        elif before.guild.id == 671078170874740756:
            offline = discord.Status.offline
            if before.status != offline and after.status == offline:
                await asyncio.sleep(120)
                if after.status == offline:
                    channel = self.bot.get_channel(686934726853787773)
                    guild = self.bot.get_guild(671078170874740756)
                    role = guild.get_role(741748857888571502)
                    message = f"\n<:offline:686955649032388623> The bot is now offline! This may be due to a restart, or it could be due to an outage! `[{datetime.utcnow().strftime('%H:%M')} UTC]`"
                    moksej_mention = f"{self.bot.get_user(345457928972533773).mention}"
                    await channel.send(message)
                    return await channel.send(moksej_mention, delete_after=1)

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
        if member.bot:
            bot_role = member.guild.get_role(674929956005871617)
            return await member.add_roles(bot_role)

        member_role = member.guild.get_role(674930044082192397)
        await member.add_roles(member_role)

        welcome_channel = member.guild.get_channel(680143582258397235)
        await welcome_channel.send(f"**{member}** has joined the server. There are now {len(member.guild.members)} members in the server.")

        await self.sync_member_roles(member=member)
        await self.process_blacklist(member=member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != 671078170874740756:
            return
        channel = discord.utils.find(lambda r: r.name == f"blacklist-{member.id}", member.guild.channels)
        if member.bot:
            return
        elif channel:
            await channel.send("They left. Banning them from the server.")
            await member.guild.ban(member, reason=f"Left without getting blacklist appeal sorted {datetime.utcnow()}")

        welcome_channel = member.guild.get_channel(680143582258397235)
        await welcome_channel.send(f"**{member}** has left the server. There are now {len(member.guild.members)} members in the server.")

    @commands.Cog.listener('on_presence_update')
    async def del_status_logging(self, before, after):  # this event is for DEL server.
        await self.bot.wait_until_ready()

        if before.guild.id != 632908146305925129:
            return

        if not before.bot:
            return

        log_channel = self.bot.get_channel(786658498175828058)
        if before.status != after.status:
            time = discord.utils.utcnow()
            if after.status == discord.Status.offline:
                await log_channel.send(f"<:offline:793508541519757352> {after.mention} - {after.name} ({after.id}) is offline! - <t:{int(time.timestamp())}> (<t:{int(time.timestamp())}:R>)")
            elif before.status == discord.Status.offline:
                await log_channel.send(f"<:online:772459553450491925> {after.mention} - {after.name} ({after.id}) is online! - <t:{int(time.timestamp())}> (<t:{int(time.timestamp())}:R>)")

#     @tasks.loop(hours=3)
#     async def update_channel_stats(self):
#         try:
#             channel1 = self.bot.get_channel(681837728320454706)
#             channel2 = self.bot.get_channel(697906520863801405)

#             head = {"Authorization": self.bot.config.DREDD_API_TOKEN, "Client": self.bot.config.DREDD_API_CLIENT}
#             data = await self.bot.session.get('https://dreddbot.xyz/api/get/stats', headers=head)
#             raw_data = await data.json()

#             await channel1.edit(name=f"Watching {raw_data['guilds']} guilds")
#             await channel2.edit(name=f"Watching {raw_data['users']} users")
#         except Exception as e:
#             ch = self.bot.get_channel(679647378210291832)
#             await ch.send(f"Failed to edit voice channels: {e}")

#     @update_channel_stats.before_loop
#     async def before_update_channel_stats(self):
#         await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Errors(bot))
