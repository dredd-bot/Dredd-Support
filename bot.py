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
import config
import datetime
import aiohttp
import sys
import asyncpg

from discord.ext import commands
from pymongo import MongoClient

sys.path.append('/home/moksej/Dredd-v3')


async def run():
    description = "A bot written in Python that uses asyncpg to connect to a postgreSQL database."
    db = await asyncpg.create_pool(**config.DB_CONN_INFO)
    mongo = MongoClient(config.MONGO_TOKEN)
    bot = Bot(description=description, db=db, mongo=mongo)
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.now()
    try:
        bot.session = aiohttp.ClientSession(loop=bot.loop)
        await bot.start(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        await bot.logout()


async def get_prefix(bot, message):
    custom_prefix = 's?'
    return commands.when_mentioned_or(custom_prefix)(bot, message)


class EditingContext(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, allowed_mentions=discord.AllowedMentions.none()):
        if file or files:
            return await super().send(content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce, allowed_mentions=allowed_mentions)
        reply = None
        try:
            reply = self.bot.cmd_edits[self.message.id]
        except KeyError:
            pass
        if reply:
            try:
                return await reply.edit(content=content, embed=embed, delete_after=delete_after, allowed_mentions=allowed_mentions)
            except Exception:
                return
        msg = await super().send(content=content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce, allowed_mentions=allowed_mentions)
        self.bot.cmd_edits[self.message.id] = msg
        return msg


intents = discord.Intents(guilds=True, messages=True, reactions=True, members=True, presences=True)


class Bot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=get_prefix,
            case_insensitive=True,
            owner_id=345457928972533773,
            reconnect=True,
            allowed_mentions=discord.AllowedMentions.none(),
            max_messages=0,
            chunk_guilds_at_startup=True,
            intents=intents
        )
        for extension in config.EXTENSIONS:
            try:
                self.load_extension(extension)
                print(f'[EXTENSION] {extension} was loaded successfully!')
            except Exception as e:
                print(f'[WARNING] Could not load extension {extension}: {e}')

        self.db = kwargs.pop('db')
        self.mongo = kwargs.pop('mongo')

        self.privacy = '<https://github.com/TheMoksej/Dredd/blob/master/PrivacyPolicy.md>'
        self.license = '<https://github.com/TheMoksej/Dredd/blob/master/LICENSE>'
        self.source = '<https://github.com/TheMoksej/Dredd-Support/>'

        self.config = config
        self.cmd_edits = {}

        self.guilds_data = {}
        self.loop = asyncio.get_event_loop()

        self.waiting_users = {}

    def get(self, k, default=None):
        return super().get(k.lower(), default)

    async def close(self):
        await self.session.close()
        await super().close()

    async def is_owner(self, user):
        if user.id == 345457928972533773:
            return True

    async def on_message(self, message):
        if message.author.bot:
            return
        try:
            ctx = await self.get_context(message, cls=EditingContext)
            if ctx.valid:
                await self.invoke(ctx)
        except Exception:
            return

    async def on_message_edit(self, before, after):

        if before.author.bot:
            return

        if after.content != before.content:
            try:
                ctx = await self.get_context(after, cls=EditingContext)
                if ctx.valid:
                    await self.invoke(ctx)
            except discord.NotFound:
                return


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
