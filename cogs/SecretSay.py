from datetime import datetime

from discord.ext import commands
import asyncio
from StateManager import StateManager, CharacterNotFound
import random
import discord
#START [Anonymous DM Dropdown]
class ChannelSelectDropdown(discord.ui.Select):
    def __init__(self,channels,client,msgData, author):
        self.client = client
        self.msg = msgData
        options=[]
        for channel in channels:
            if type(channel) is discord.TextChannel:                                                                    # Only allowed to be sent in text channels
                if channel.permissions_for(author).send_messages:                                                       # Only allow the use of channels with permission to send in said channel
                    options.append(discord.SelectOption(label=channel.name, value=channel.id))

        super().__init__(
            placeholder="Choose channel...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):                                                         # Called on selection
        channelSelection = self.client.get_channel(int(self.values[0]))
        await channelSelection.send(content=self.msg.content,
                                    embeds=self.msg.embeds,
                                    files=[await attch.to_file() for attch in self.msg.attachments])                    # Forward all information received (todo, check audio, etc)
        await interaction.response.send_message('Sent.')

class CSDropdownView(discord.ui.View):
    def __init__(self,channels, client, msg, author):
        super().__init__()
        self.add_item(ChannelSelectDropdown(channels, client, msg, author))                                             # Add the dropdown to our view object.
#END [Anonymous DM Dropdown]


class SecretSay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author in self.bot.serverA.members




    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            if message.author == self.bot.user:  # Ignore messages sent by self (the bot) #TODO unsure if necessary
                return
            # Handle DM's                                                       # I hate iterating through the loop but this prevents us from passing a 'User' rather than 'Member" hopefully
            #TODO put this in bot so that we dont have to build this list every message
            channelsClean = [x for x in self.bot.serverA.channels if x not in self.bot.yipyapCategory.channels]
            if message.author in self.bot.serverA.members:
                # TODO: fallback to text messages if more than 25 ? Pagination functionality?
                view = CSDropdownView(channelsClean, self, message, message.author)                                      # Create a view that has a dropdown and that calls our message send
                await message.channel.send("Select Channel:", view=view)                                    # Sending a message containing our view
                return

async def setup(bot):
    await bot.add_cog(SecretSay(bot))