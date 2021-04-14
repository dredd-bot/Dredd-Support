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
import asyncio
import traceback

from discord.ext import commands
from datetime import datetime, timezone
from contextlib import suppress

from io import BytesIO
from utils import default, publicflags

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def open_ticket(self, guild, user):
        category = self.bot.get_channel(783682371953098803)
        support = guild.get_role(679647636479148050)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            support: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_permissions=True, manage_channels=True)
        }

        channel = await category.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites,
                                                     reason=f"Support ticket channel - {user.id}",
                                                     topic=f"User ID: {user.id}")
        await self.bot.db.execute("INSERT INTO tickets(user_id, status, ticket_channel) VALUES($1, $2, $3)", user.id, 0, channel.id)
        fetch_tickets = "SELECT count(*) FROM tickets"
        ticket_id = await self.bot.db.fetchval(fetch_tickets)
        print(ticket_id)

        def checks(r, u):
            return u.id == user.id and r.message.id == subject_message.id
        
        reactions_dict = {
            '❓': "General Question",
            "<:privacy:733465503594708992>": "Privacy policy concerns or data deletion request",
            "<:p_:748833273383485440>": "Partnership Application",
            "🐛": "Bug report",
            "<:unban:687008899542286435>": "Blacklist Appeal"
        }

        channel_dict = {
            '❓': "question-",
            "<:privacy:733465503594708992>": "privacy-",
            "<:p_:748833273383485440>": "partner-",
            "🐛": "bug-",
            "<:unban:687008899542286435>": "appeal-"
        }
        
        subject_message = await channel.send(f"{user.mention} Please choose the subject of your ticket.\n\n"
                                             "❓ General Question\n<:privacy:733465503594708992> Privacy policy concerns - data deletion request\n"
                                             f"<:p_:748833273383485440> Partnership application\n🐛 Bug report\n"
                                             f"<:unban:687008899542286435> Blacklist appeal", allowed_mentions=discord.AllowedMentions(users=True))
        for reaction in reactions_dict:
            await subject_message.add_reaction(reaction)
        try:
            loop = True
            while loop:
                react, user = await self.bot.wait_for('reaction_add', check=checks, timeout=60.0)

                if str(react) not in reactions_dict:
                    await subject_message.remove_reaction(react)
                elif str(react) in reactions_dict:
                    loop = False
                    subject = reactions_dict[str(react)]
                    await channel.edit(name=f"{channel_dict[str(react)]}{user.name}")   
                    await subject_message.delete()
        except Exception as e:
            error_log_channel = guild.get_channel(675742172015755274)
            error = traceback.format_exception(type(e), e, e.__traceback__) 
            try:
                await error_log_channel.send(f"Error occured in the ticket: ```py\n{error}```")
            except Exception:
                pass
            loop = False
            subject = reactions_dict['❓']
            await channel.edit(name=f"{channel_dict['❓']}{user.name}")   
            await subject_message.delete()
            await channel.send("You took too long, setting subject automatically.", delete_after=20)
             
        ticket_embed = discord.Embed(color=14715915, title=f'New Ticket Opened (ID: `{ticket_id}`)', timestamp=datetime.now(timezone.utc))
        ticket_embed.set_author(name=user, icon_url=user.avatar_url)
        ticket_embed.description = "Thanks for creating this support ticket! " \
                                   "Please leave your message below " \
                                   "and wait for an answer from one of the support team members.\n" \
                                   f"**Ticket Subject:** {subject}"
        ticket_embed.set_footer(text=f"Ticket #{ticket_id}")
        ticket_pin = await channel.send(embed=ticket_embed)
        permissions_dict = discord.PermissionOverwrite()
        permissions_dict.send_messages = True
        permissions_dict.read_messages = True
        await channel.set_permissions(user, overwrite=permissions_dict)
        await ticket_pin.pin()
        ticket_type = 1 if subject == reactions_dict['❓'] else 2 if subject == reactions_dict['<:privacy:733465503594708992>'] else 3 if subject == reactions_dict['<:p_:748833273383485440>'] else 4 if subject == reactions_dict['🐛'] else 5

        try:
            await user.send(f"I've successfully created your ticket `#{ticket_id}` and set the subject to: {subject}")
        except Exception:
            pass

        log_embed = discord.Embed(color=2007732, timestamp=datetime.now(timezone.utc))
        log_embed.set_author(name=f"Ticket opened by {user} ({user.id})", icon_url=user.avatar_url)
        log_embed.description = f"**Ticket Subject:** {subject}"
        log_embed.add_field(name="Channel:", value=channel.mention)
        log_embed.add_field(name="User:", value=f"[{user}](https://discord.com/users/{user.id})")
        log_embed.set_footer(text=f"Ticket #{ticket_id}")
        log_channel = self.bot.get_channel(783683451480047616)
        log_msg = await log_channel.send(content="<@&679647636479148050>", embed=log_embed, allowed_mentions=discord.AllowedMentions(roles=True))
        query = 'UPDATE tickets SET ticket_type = $1, log_message = $2, ticket_pin = $3, ticket_id = $4 WHERE user_id = $5 AND status = $6'
        await self.bot.db.execute(query, ticket_type, log_msg.id, ticket_pin.id, ticket_id, user.id, 0)

    async def close_ticket(self, ticket_channel, ticket_id, user, mod, force, reason):
        try:
            def check(c):
                return c.channel.id == ticket_channel.id
            
            if not force:
                confirm_message = await ticket_channel.send("Deleting ticket in 15 seconds. To abort please send a message below.")

                try:
                    confirm_close = await self.bot.wait_for('message', check=check, timeout=15.0)

                    if confirm_close:
                        return await confirm_message.edit(content='Not closing the ticket.')
                except Exception:
                    await confirm_message.edit(content="Closing ticket...")
            else:
                await ticket_channel.send("Forcefully deleting the ticket.")                               

            ticket_info = await self.bot.db.fetchval("SELECT log_message FROM tickets WHERE ticket_channel = $1", ticket_channel.id)
            log_message = await self.bot.get_channel(783683451480047616).fetch_message(ticket_info)
            messages = []
            for message in await ticket_channel.history().flatten():
                messages.append(f"[{message.created_at}] {message.author} - {message.content}\n")

            messages.reverse()
            file = discord.File(BytesIO(("".join(messages)).encode("utf-8")), filename=f"ticket-{ticket_id}.txt")

            log_channel = self.bot.get_channel(703653345948336198)
            log_file = await log_channel.send(content=f"{log_message.jump_url}", file=file)
            url = f"https://txt.discord.website/?txt={log_channel.id}/{log_file.attachments[0].id}/ticket-{ticket_id}"
            
            embed = log_message.embeds[0]
            embed.color = 13388105
            embed.remove_field(0)
            embed.insert_field_at(0, name="Channel:", value=f"[#{ticket_channel.name}]({url})")
            embed.description += f"\n**Ticket closed by:** {mod} ({mod.id})\n**Reason:** {reason}"
            await log_message.edit(embed=embed)
            await ticket_channel.delete(reason=f'Ticket closed by {mod} ({mod.id}) - {reason}')
            query = 'UPDATE tickets SET status = $1, reason = $2 WHERE ticket_channel = $3'
            await self.bot.db.execute(query, 1, reason, ticket_channel.id)

            send_embed = discord.Embed(color=13388105, title='Ticket Closed!', timestamp=datetime.now(timezone.utc))
            send_embed.set_author(name=mod, icon_url=mod.avatar_url)
            send_embed.description = f"Hey!\n{mod} closed your ticket for: {reason}.\n" \
                                     f" You can look at the full ticket transaction by [`clicking here`]({url})"
            send_embed.set_footer(text=f'Your ticket id was #{ticket_id}')
            
            try:
                user = self.bot.get_user(user)
                await user.send(embed=send_embed)
            except Exception as e:
                print(e)
                return          

        except Exception as e:
            print('error: ' + e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id != 671078170874740756:
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        channel = payload.member.guild.get_channel(783445230502019142)
        message = await channel.fetch_message(783696042376822795)
        check = await self.bot.db.fetchval("SELECT ticket_channel FROM tickets WHERE user_id = $1 AND status = $2", user.id, 0)

        if payload.message_id == 783696042376822795:
            await message.remove_reaction(payload.emoji, payload.member)
            if str(payload.emoji) == '🎫':
                if check:
                    try:
                        return await user.send(f"Hey! You already have a support ticket opened at {self.bot.get_channel(check).mention}.")
                    except Exception:
                        return
                await self.open_ticket(guild, user)

    @commands.command(name='close-ticket',
                      aliases=['closeticket', 'close'])
    @commands.guild_only()
    @commands.has_role(679647636479148050)
    async def closeticket(self, ctx, *, reason: str):
        """ Close a support ticket """
        check = await self.bot.db.fetch("SELECT user_id, ticket_id FROM tickets WHERE ticket_channel = $1", ctx.channel.id)
        force = False
        if reason.lower().startswith('-f'):
            reason = reason[3:]
            force = True

        if not check:
            return await ctx.send(f"This channel isn't a ticket.", delete_after=15)
        elif check:
            await self.close_ticket(ctx.channel, check[0]['ticket_id'], check[0]['user_id'], ctx.author, force, reason)

    @commands.group(name='partner', invoke_without_command=True)
    @commands.guild_only()
    @commands.has_role(674929900674875413)
    async def partner(self, ctx):
        await ctx.send_help(ctx.command)

    @partner.command(name='add-bot', aliases=['bot', 'user', 'abot'])
    @commands.guild_only()
    @commands.has_role(674929900674875413)
    async def partner_add_bot(self, ctx, member: discord.Member, bot: commands.Greedy[discord.User, str]):
        bot = await default.find_user(ctx, bot)
        if member.bot:
            return await ctx.send(f"<:warning:820339642884030475> {member} is a bot. Please provide a non-bot user id.")
        if not bot.bot:
            return await ctx.send(f"<:warning:820339642884030475> {bot} is not a bot. Please provide a bot user id.")

        part_check = await self.bot.db.fetchval("SELECT * FROM partners WHERE bot_id = $1", bot.id)
        if part_check:
            return await ctx.send(f"<:warning:820339642884030475> {bot} is already partnered.")
        try:
            support_server = self.bot.get_guild(671078170874740756)
            partner_channel = support_server.get_channel(679647378210291832)
            partner_role = support_server.get_role(683288670467653739)
            new_partners_notif = support_server.get_role(741749103280783380)
            partner_member = support_server.get_member(member.id)
            partner_main_chat = support_server.get_channel(679647378210291832)

            await ctx.channel.send("Please send a partner message (must be shorter than 1500 characters)")
            while True:
                message, user = await self.bot.wait_for('message', check=lambda c, m: c.channel.id == ctx.channel.id and m.id == ctx.author.id, timeout=60)

                if len(message) > 1500:
                    await ctx.channel.send(f"Message is {len(message) - 1500} characters longer than the limit, please shorten it.", delete_after=5)
                    continue
                elif len(message) < 1500:
                    message = message
                    await message.delete()
                    break
            
            e = discord.Embed(color=5622378, title="Please verify the message is correct", description=message)
            e.add_field(name='Bot information:', value=f"**Name & ID:** {bot} ({bot.id})\n**Created:** {default.human_timedelta(bot.created_at.replace(tzinfo=None))}")
            reactions = ['<:yes:820339603722600470>', '<:no:820339624849178665>']
            message = await ctx.channel.send(content=f"{ctx.author.mention} - {member.mention}", embed=e, allowed_mentions=discord.AllowedMentions(users=True))

            for reaction in reactions:
                await message.add_reaction(reaction)
            
            while True:
                reaction, user = await self.bot.wait_for('reaction_add', check=lambda r, m:  r.message.id == message.id and m.id in [ctx.author.id, user.id], timeout=60)

                if str(reaction) == '<:yes:820339603722600470>':
                    break
                elif str(reaction) == '<:no:820339624849178665>':
                    return await ctx.channel.send("Cancelled the command.")
                else:
                    await message.remove_reaction(str(reaction))

            badges = await self.bot.db.fetchval("SELECT * FROM badges WHERE _id = $1", user.id)
            flags = publicflags.BotFlags(badges)
            if 'bot_partner' not in [*flags] and badges:
                await self.bot.db.execute("UPDATE badges UPDATE flags = flags + 4", user.id)
            elif not badges:
                await self.bot.db.execute("INSERT INTO badges(_id, flags) VALUES($1, $2)", user.id, 4)
            else:
                pass

            if partner_member and partner_role not in partner_member.roles:
                await partner_member.add_roles(partner_role, reason='user is now a our partner!')
                await partner_main_chat.send(f"<:p_:748833273383485440> Welcome **{member.mention}** to our bot partners list!", allowed_mentions=discord.AllowedMentions(users=True))

            message = await partner_channel.send(f"{new_partners_notif.mention}\n\n{message}")
            await self.bot.db.execute("INSERT INTO partners(_id, type, message, time, bot_id, message_id) VALUES($1, $2, $3, $4, $5, $6)", user.id, 0, message.content[24:], datetime.utcnow(), bot.id, message.id)
            mongo_db = self.bot.mongo.get_database('website')
            mongo_db.partners.insert_one({
                'partner_user': member.id,
                'partner_bot': bot.id,
                'short_msg': "No message set...",
                'website': "https://discord.com/oauth2/authorize?client_id={0}&scope=bot&permissions=0".format(bot.id),
                'partner_since': datetime.utcnow(),
                'html': "No description set..."
            })
            try:
                await member.send(f"<:p_:748833273383485440> Congratulations! We're officially partners now!"
                                   "\nI've added a badge to your badges (you can see them in `-badges`), you can also see your partnering information in `-partnerslist`. "
                                   "To get your information updated on the site (https://dredd-bot.xyz/partners) please DM Moksej a short brief (<150 chars), "
                                   "long description (html), link to website/docs/anything you want.")
            except Exception:
                pass

            await ctx.channel.send("Done!~")

        except asyncio.TimeoutError:
            return await ctx.send("You ran out of time.")

        except Exception as e:
            return await ctx.send(default.traceback_maker(e, advance=True))

    @partner.command(name='add-server', aliases=['server', 'guild', 'aserver'])
    @commands.guild_only()
    @commands.has_role(674929900674875413)
    async def partner_add_server(self, ctx, member: discord.Member):

        try:
            message = await ctx.channel.send("Have you verified if Dredd is in the server?", delete_after=60)
            reactions = ['<:yes:820339603722600470>', '<:no:820339624849178665>']

            for reaction in reactions:
                    await message.add_reaction(reaction)

            in_guild, valid = None, None         
            while True:
                reaction, user = await self.bot.wait_for('reaction_add', check=lambda r, m: r.message.id == message.id and m.id == ctx.author.id, timeout=60)

                if str(reaction) == '<:yes:820339603722600470>':
                    in_guild, valid = True, True
                    await message.delete()
                    break
                elif str(reaction) == '<:no:820339624849178665>':
                    in_guild = False
                    await message.delete()
                    break
                else:
                    await message.remove_reaction(str(reaction))
                    continue

            guild, invite = None, None
            if not in_guild:
                message = await ctx.channel.send("Please send a permanent invite to the server if you want to validate the partnership without Dredd being in that server.")
                while True:
                    message, user = await self.bot.wait_for('message', check=lambda c, m: c.channel.id == ctx.channel.id and m.id == ctx.author.id, timeout=60)

                    if message.content.lower() == 'cancel':
                        break

                    try:
                        guild = await self.bot.fetch_invite(message)
                        invite = guild.url
                        guild = guild.guild.id
                        break
                    except Exception as e:
                        await ctx.channel.send(f"Error occured: `{e}`")
                        continue
                
                if not guild:
                    return
            elif in_guild:
                message = await ctx.channel.send("Please send an ID of the server you want to partner")
                while True:
                    message, user = await self.bot.wait_for('message', check=lambda c, m: c.channel.id == ctx.channel.id and m.id == ctx.author.id, timeout=60)

                    if message.content.lower() == 'cancel':
                        break

                    database_check = await self.bot.db.fetchval("SELECT * FROM guilds WHERE guild_id = $1", int(message))
                    if not database_check:
                        await ctx.channel.send(f"Dredd doesn't seem to be in that server. Please make sure the id is correct")
                        continue
                    else:
                        guild = int(message)
                        break
                if not guild:
                    return

            await ctx.send("Send a partner message that should be sent to the partners channel. (must be shorter than 1500 characters)")
            while True:
                message, user = await self.bot.wait_for('message', check=lambda c, m: c.channel.id == ctx.channel.id and m.id == ctx.author.id, timeout=60)

                if len(message) > 1500:
                    await ctx.channel.send(f"Message is {len(message) - 1500} characters longer than the limit, please shorten it.", delete_after=5)
                    continue
                elif len(message) < 1500:
                    message = message
                    await message.delete()
                    break
            
            e = discord.Embed(color=5622378, title="Please verify the message is correct", description=message)
            e.add_field(name='Guild information:', value=f"**Guild:** {guild}\n**Created:** {default.human_timedelta(guild.created_at.replace(tzinfo=None))}")
            reactions = ['<:yes:820339603722600470>', '<:no:820339624849178665>']
            message = await ctx.channel.send(content=f"{ctx.author.mention} - {member.mention}", embed=e, allowed_mentions=discord.AllowedMentions(users=True))
            for reaction in reactions:
                await message.add_reaction(reaction)
            
            while True:
                reaction, user = await self.bot.wait_for('reaction_add', check=lambda r, m:  r.message.id == message.id and m.id in [ctx.author.id, member.id], timeout=60)

                if str(reaction) == '<:yes:820339603722600470>':
                    break
                elif str(reaction) == '<:no:820339624849178665>':
                    return await ctx.channel.send("Cancelled the command.")
                else:
                    await message.remove_reaction(str(reaction))
                    continue
            
            support_server = self.bot.get_guild(671078170874740756)
            partner_channel = support_server.get_channel(679647378210291832)
            partner_role = support_server.get_role(683288670467653739)
            new_partners_notif = support_server.get_role(741749103280783380)
            partner_main_chat = support_server.get_channel(679647378210291832)

            badges = await self.bot.db.fetchval("SELECT * FROM badges WHERE _id = $1", member.id)
            flags = publicflags.BotFlags(badges)
            if 'bot_partner' not in [*flags] and badges:
                await self.bot.db.execute("UPDATE badges UPDATE flags = flags + 4", member.id)
            elif not badges:
                await self.bot.db.execute("INSERT INTO badges(_id, flags) VALUES($1, $2)", member.id, 4)
            else:
                pass

            if member and partner_role not in member.roles:
                await member.add_roles(partner_role, reason='user is now a our partner!')
                await partner_main_chat.send(f"<:p_:748833273383485440> Welcome **{member.mention}** to our servers partners list!", discord.AllowedMentions(users=True))
            
            message = await partner_channel.send(f"{new_partners_notif.mention}\n\n{message}")
            if invite:
                que = "INSERT INTO partners(_id, type, message, time, message_id, valid, invite) VALUES($1, $2, $3, $4, $5, $6, $7)"
                await self.bot.db.execute(que, guild, 1, message.content[24:], datetime.utcnow(), message.id, valid, invite)
            else:
                que = "INSERT INTO partners(_id, type, message, time, message_id) VALUES($1, $2, $3, $4, $5)"
                await self.bot.db.execute(que, guild, 1, message.content[24:], datetime.utcnow(), message.id)
            try:
                await member.send(f"<:p_:748833273383485440> Congratulations! We're officially partners now!"
                                   "\nI've added a badge to your badges (you can see them in `-badges`), you can also see your partnering information in `-partnerslist`.")
            except Exception:
                pass

            await ctx.channel.send("Done!~")

        except asyncio.TimeoutError:
            return await ctx.send("You took too long, cancelling the command.")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e, advance=True))

    @partner.command(name='remove-server', aliases=['rserver', 'rguild'])
    @commands.guild_only()
    @commands.has_role(674929900674875413)
    async def partner_remove_server(self, ctx, server_id: int, *, reason: str):

        check = self.bot.db.fetch("SELECT message_id FROM partners WHERE _id = $1", server_id)

        if not check:
            return await ctx.send(f"Can't find {server_id} in the partners list.")
        elif check:
            support_server = self.bot.get_guild(671078170874740756)
            partner_channel = support_server.get_channel(679647378210291832)
            partner_main_chat = support_server.get_channel(679647378210291832)

            with suppress(discord.errors.NotFound):
                msg = await partner_channel.fetch_message(check['message_id'])
                await msg.delete()
            
            await self.bot.db.execute('DELETE FROM partners WHERE _id = $1', server_id)
            await partner_main_chat.send(f"{server_id} has been removed from my partner's list for `{reason}`")
            await ctx.send(f"Successfully removed {server_id} from my partners list.")

    @partner.command(name='remove-bot', aliases=['rbot'])
    @commands.guild_only()
    @commands.has_role(674929900674875413)
    async def partner_remove_bot(self, ctx, bot: commands.Greedy[discord.User, str], *, reason: str):
        bot = await default.find_user(ctx, bot)

        if not bot:
            return await ctx.send(f"Couldn't find a bot with that name or id.")
        elif bot and not bot.bot:
            return await ctx.send(f"Please provide me a bot, not a normal user")
        elif bot and bot.bot:
            check = self.bot.db.fetch("SELECT message_id, _id FROM partners WHERE bot_id = $1", bot.id)

            if not check:
                return await ctx.send(f"{bot} doesn't seem to be a partner.")
            elif check:
                support_server = self.bot.get_guild(671078170874740756)
                partner_channel = support_server.get_channel(679647378210291832)
                partner_main_chat = support_server.get_channel(679647378210291832)
                partner_role = support_server.get_role(683288670467653739)

                with suppress(discord.errors.NotFound):
                    msg = await partner_channel.fetch_message(check['message_id'])
                    await msg.delete()
                
                member = await self.bot.get_user(check['_id'])
                if member:
                    with suppress(Exception):
                        await member.send("Unfortunately, we've decided to no longer be partners with you, sorry for the inconvenience and thanks for being our partner since now :)"
                                          f"\n**Reason:** {reason}")

                badges = await self.bot.db.fetchval("SELECT * FROM badges WHERE _id = $1", check['_id'])
                if badges:
                    await self.bot.db.execute("UPDATE partners SET flags = flags - 4 WHERE _id = $1", check['_id'])
                
                mongo_db = self.bot.mongo.get_database('website')
                mongo_db.partners.delete_one({"partner_bot": bot.id})
                await self.bot.db.execute('DELETE FROM partners WHERE bot_id = $1', bot.id)
                await partner_main_chat.send(f"{server_id} has been removed from my partner's list.")
                await ctx.send(f"Successfully removed {server_id} from my partners list.")


def setup(bot):
    bot.add_cog(Tickets(bot))
