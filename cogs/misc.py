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

from discord.ui import View, button as buttons, Button
from discord.ext import commands
from datetime import datetime, timedelta


class ReactionRoles(View):
    def __init__(self, bot):
        self.bot = bot

        super().__init__(timeout=None)

    @buttons(label="Announcements", style=discord.ButtonStyle.green, custom_id="dredd_support:announcements_role")
    async def announcements(self, button: Button, interaction: discord.Interaction):
        role = interaction.guild.get_role(741748979917652050)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            return await interaction.response.send_message(f"Removed {role.mention} from your roles.", ephemeral=True)
        await interaction.user.add_roles(role)
        return await interaction.response.send_message(f"Added {role.mention} to your roles.", ephemeral=True)

    @buttons(label="Partners", style=discord.ButtonStyle.blurple, custom_id="dredd_support:partners_role")
    async def partners(self, button: Button, interaction: discord.Interaction):
        role = interaction.guild.get_role(741749103280783380)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            return await interaction.response.send_message(f"Removed {role.mention} from your roles.", ephemeral=True)
        await interaction.user.add_roles(role)
        return await interaction.response.send_message(f"Added {role.mention} to your roles.", ephemeral=True)

    @buttons(label="Status", style=discord.ButtonStyle.red, custom_id="dredd_support:status_role")
    async def status(self, button: Button, interaction: discord.Interaction):
        role = interaction.guild.get_role(741748857888571502)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            return await interaction.response.send_message(f"Removed {role.mention} from your roles.", ephemeral=True)
        await interaction.user.add_roles(role)
        return await interaction.response.send_message(f"Added {role.mention} to your roles.", ephemeral=True)

    @buttons(label="Updates", style=discord.ButtonStyle.gray, custom_id="dredd_support:updates_role")
    async def updates(self, button: Button, interaction: discord.Interaction):
        role = interaction.guild.get_role(840624312628412447)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            return await interaction.response.send_message(f"Removed {role.mention} from your roles.", ephemeral=True)
        await interaction.user.add_roles(role)
        return await interaction.response.send_message(f"Added {role.mention} to your roles.", ephemeral=True)


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if self.bot.is_ready():
            bot.add_view(ReactionRoles(self.bot))

    def cog_unload(self) -> None:
        self.bot.remove_view(ReactionRoles(self.bot))

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ReactionRoles(self.bot))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reactions(self, ctx, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        e = discord.Embed(color=discord.Color.blurple(), title="Role Menu")
        e.description = f"""
        Add yourself a role so you'd get notified for things such as: status reports, new partnerships, announcements, bot updates
        
        Announcements - {ctx.guild.get_role(741748979917652050).mention} - Get notified about important announcements
        Partners - {ctx.guild.get_role(741749103280783380).mention} - Get notified about new partnerships
        Status - {ctx.guild.get_role(741748857888571502).mention} - Get notified about Dredd's status report
        Updates - {ctx.guild.get_role(840624312628412447).mention} - Get notified about new updates
        """
        view = ReactionRoles(self.bot)
        await channel.send(embed=e, view=view)

    @commands.command(brief='Privacy policy', aliases=['pp', 'policy', 'privacypolicy'])
    async def privacy(self, ctx):
        e = discord.Embed(color=discord.Color.blurple(), title=f"{self.bot.user} Privacy Policy's")
        e.add_field(name='What data is being stored?', value="Your user id is being stored if you open a ticket in <#783445230502019142>. For more details you can read"
                                                             " [this](https://github.com/dredd-bot/Dredd/blob/master/privacy.md 'privacy policy') as both bots share the same database", inline=False)
        e.add_field(name='What should I do if I have any concerns?', value=f"You can shoot a direct message to **{ctx.guild.owner}**, open a support ticket in <#783445230502019142> or email us at `support@dreddbot.xyz`")
        await ctx.send(embed=e)

    @commands.command(name='time', brief='Displays Moksej\'s time')
    async def time(self, ctx):
        get_time = datetime.now()
        await ctx.send(f"Current <@345457928972533773>'s time is: {get_time.strftime('%H:%M')} CET (Central European Time)", allowed_mentions=discord.AllowedMentions(users=False))

    @commands.command(name='requirements')
    @commands.guild_only()
    async def requirements(self, ctx):
        """ Requirements to partner a bot or a server """
        message = """**Server:**
> • Must not violate Discord's Terms of Service
> • Must have at least 100 members
> • Must have Dredd in the server
> • Must be SFW
> • Preferably a community server

**Bot:**
> • Must not violate Discord's Terms of Service
> • Must have at least 100 servers
> • Main purpose must not be NSFW
> • Must have SFW name and avatar
> • Must have a support server
> • Must not be a copy of another bot.
> • Preferably verified by discord
> • Doesn't ask for administrator in invite

*Note: Moksej may and may not let you partner with or without these requirements. Our partnership can be discontinued at any given time.*"""

        await ctx.send(message)

    @commands.command(name='partner-message', aliases=['partnermessage', 'partnermsg', 'pmsg'])
    @commands.guild_only()
    async def partner_message(self, ctx):
        """ Returns our partner message """
        return await ctx.send("You can find our partner message here: <https://github.com/dredd-bot/Dredd/blob/master/partners.md>")


def setup(bot):
    bot.add_cog(Utils(bot))
