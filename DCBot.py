"""
DCBot
A bot that manages different functionality for 2 discord servers, referred to as ServerA and ServerB.

[General Functionality]:
    * Allow users to send anonymous messages/replies using /secret or /secretreply
    * Snitch switch, which prints who says what for the afore mentioned functionality
    * Allows users without elevated permissions to pin messages by reacting to a message with a pin emoji
    * Delete all messages from a channel using /manualPurge

[ServerA Functionality]:
    * Periodically wipe a "whiteboard" channel at a set time daily.
    * Extended anonymous functionality as described in [General Functionality], with the addition of the option to DM the bot
      to send a message, which allows media to be sent as well.

[ServerB Functionality]:
    * Act as a mute switch for two users/bots via /timeoutmomdad, which turns their mute switch on/off

Possible future functionality:
    * Ability to go back and retrieve messages from DMs?
    * Enumerate+print guild perms, to troubleshoot why functionality in one server might work and the other not?
    * Combination of repudiation tracker for a 3rd server, serverC (would need to remove anonymous functionality for serverC)

TODO:
    [ ]
"""

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import time
from tzlocal import get_localzone

#START [Config Values]
# Misc. config
localTimeZone = get_localzone()                                                                                         # The local time zone for use in scheduling
# General config
godID = "[REDACTED]"                                                                                                    # Owner ID (Allows access to private commands etc...)
snitch = True                                                                                                           # Is snitch mode enabled on the bot
# ServerA config
serverAID = "[REDACTED]"                                                                                                # ServerA ID
serverAWhiteboardID = "[REDACTED]"                                                                                      # Channel to be periodically wiped for ServerA
wipeTime = time(3, 45, 0, tzinfo=localTimeZone)
# ServerB config
serverBID = "[REDACTED]"                                                                                                # ServerB ID
dadBotMomBotIDs = ["[REDACTED]","[REDACTED]"]                                                                           # Bot ID's for Mom and Dad
dadBotMomBotChannelIDs = ["[REDACTED]","[REDACTED]"]                                                                    # Channel ID's that mom/dad can talk in
# Intents config
# We don't need all of these, however I choose to give the bot all intents to
# simplify the addition of features in the future.
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions=True
intents.messages = True
intents.presences = True
intents.emojis = True
#END [Config Values]

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

#START [Bot Core]
class DCBot(commands.Bot):
    def __init__(self):
        self.serverBBotsOff = True                                                                                      # Should mom and dad be muted in Waffle Mania
        self.authorizedDMSenders=[]                                                                                     # List of users who may message the bot to privately send messages in Server A.
        super().__init__(command_prefix='/', intents=intents)

    async def setup_hook(self):
        self.cleanWhiteboard.start()                                                                                    # Activate the "cleanWhiteboard" functionality, which attempts to clear a channel of all messages daily at a given time.
        print('[setup_Hook complete]')
    async def on_ready(self):
        for member in self.get_guild(serverAID).members:
            self.authorizedDMSenders.append(member.id)
        print(f"[on_ready complete]\nSnitch mode: {snitch}\nLogged in as {self.user}")

#START [Event Handlers]
    async def on_message(self,message):
        if message.author == self.user:                                                                                 # Ignore messages sent by self (the bot) #TODO unsure if necessary
            return
        if not message.guild:                                                                                           # Handle DM's
            if snitch:                                                                                                  # Print user message if snitch is on
                print(message.author.name + "> \"" + message.content + "\"")
            serverA = self.get_guild(serverAID)
            for member in serverA.members:                                                                              # I hate iterating through the loop but this prevents us from passing a 'User' rather than 'Member" hopefully
                if member == message.author:
                    # TODO: fallback to text messages if more than 25 ? Pagination functionality?
                    view = CSDropdownView(serverA.channels, self, message, member)                                      # Create a view that has a dropdown and that calls our message send
                    await message.channel.send("Select Channel:", view=view)                                    # Sending a message containing our view
                    return
        else:
            if message.guild.id==serverBID:                                                                             # If not DM, check if it's a mom/dad message in server B
                if (message.channel.id not in dadBotMomBotChannelIDs
                    and message.author.id in dadBotMomBotIDs
                    and self.serverBBotsOff):                                                                           # We only care if 1) it's not in the mom dad channel, 2) it's mom or dad, and 3) the bots are set to off
                        await message.delete()
        await bot.process_commands(message)                                                                             # Pass on commands

    async def on_raw_reaction_add(self, payload):
        # PIN-IT add functionality.
        # Pins a message if there is one or more "📌" reaction added.
        # Allows pinning as a group and without perms
        if payload.emoji.name =='📌':
            msg = await self.get_channel(payload.channel_id).fetch_message(payload.message_id)
            for reaction in msg.reactions:
                if reaction.emoji == '📌' and reaction.count == 1:                                                      # Only pin on the first instance of getting the reaction. No need to waste calls.
                    try:
                        await msg.pin()
                        return
                    except Exception as e:#TODO
                        print("Exception")
    async def on_raw_reaction_remove(self, payload):
        # PIN-IT remove functionality.
        # Un-pins a message if there are 0 "📌" reactions after a reaction removal.
        if payload.emoji.name == '📌':
            msg = await self.get_channel(payload.channel_id).fetch_message(payload.message_id)
            for reaction in msg.reactions:
                if reaction.emoji == '📌':                                                                              # If we see even one pin, it's still pinned, so we can just quit after seeing a pin.
                    return
            try:                                                                                                        # We only hit this if we never see a pin
                await msg.unpin()
            except Exception as e:
                print("Exception")#TODO
            return
#END [Event Handlers]

#START [Tasks]
    #ServerA whiteboard functionality
    @tasks.loop(time=wipeTime)
    async def cleanWhiteboard(self): #TODO possible issues with calling delete_messages in certain circumstances (old messages, lots of messages?)
        chatCleared = False
        while not chatCleared:
            whiteboardChannel = self.get_channel(serverAWhiteboardID)
            messagesToDelete = []
            async for message in whiteboardChannel.history(oldest_first=True):
                messagesToDelete.append(message)
            if len(messagesToDelete) == 0:
                chatCleared = True
                await whiteboardChannel.send('Whiteboard clean.')
            await whiteboardChannel.delete_messages(messagesToDelete)

    @cleanWhiteboard.before_loop
    async def beforeCleanWhiteboard(self):
        await self.wait_until_ready()                                                                                   # Wait until the cache is populated
#END [Tasks]
#END [Bot Core]

bot = DCBot()

#START [Private Commands]
# Synchronization commands, registered not as typical hybrid commands but as internal commands to prevent them from
# showing up in the command list.
@bot.command()
async def syncglobal(ctx):
    if ctx.author.id == godID:
        await bot.tree.sync()
        await ctx.send('Synced Commands Globally')

@bot.command()
async def sync(ctx): #Todo make this sync to the server im sending this from?
    if ctx.author.id == godID:
        bot.tree.copy_global_to(guild=discord.Object(id =serverAID))
        await bot.tree.sync(guild=discord.Object(id =serverAID))
        await ctx.send('Synced to serverA')

@bot.command()
async def manualPurge(ctx): #TODO would it be easier to just delete a channel and recreate it instead of wiping each emssage?
    if ctx.author.id == godID:
        messagesToDelete = []
        async for message in ctx.channel.history(oldest_first=True):
            messagesToDelete.append(message)
        try:
            await ctx.channel.delete_messages(messagesToDelete)
        #TODO unsure about this
        except Exception as e:                                                                                          # If we hit an exception, try to manually delete the messages one-by-one
            for message in messagesToDelete:
                await message.delete()
                await asyncio.sleep(0.5)                                                                                # Rate limit
        await ctx.channel.send('Chat Purged.')

@bot.hybrid_command()
async def selfdestruct(ctx):                                                                                            # Leaves all guilds
    if ctx.author.id == godID:
        for guild in bot.guilds:
            #Todo: add a goodbye message?
            await guild.leave()
#END [Private Commands]

#START [General Commands]
@bot.hybrid_command()
async def secret(ctx, *, message: str):                                                                                 # The asterisk is needed to handle spaces in the message
    if ctx.interaction is None:                                                                                         # This is to handle outdated clients, deleting their use of the command from the chat.
        await ctx.message.delete()
    if snitch:
        print(ctx.message.author.name +"> \""+message +"\"")                                                            # Print the author and their message if snitch-mode is active
    await ctx.channel.send(message)
    await ctx.reply("Sent.", ephemeral=True)                                                                            # Must acknowledge ctx

@bot.hybrid_command()
async def secretreply(ctx, *, message: str, id:str):                                                                    # The asterisk is needed to handle spaces in the message
    id=int(id)                                                                                                          # Convert from an input string to integer for use as a proper ID
    if ctx.interaction is None:                                                                                         # This is to handle outdated clients, deleting their use of the command from the chat.
        await ctx.message.delete()
    if snitch:                                                                                                          # Print the author and their message if snitch-mode is active
        print(ctx.message.author.name +"> \""+message +"\"")
    await ctx.channel.send(message,reference=await ctx.fetch_message(id))
    await ctx.reply("Sent.", ephemeral=True)                                                                            # Must acknowledge ctx
#END [General Commands]

#START [ServerB Commands]
@bot.hybrid_command()
async def timeoutmomdad(ctx): #todo change name?
    if ctx.guild is not None and ctx.guild.id==serverBID:                                                               # Only should be called if used within ServerB.
        if bot.serverBBotsOff:
            bot.serverBBotsOff = False
            await ctx.interaction.response.send_message("Mom and Dad are now un-muted.")
        else:
            bot.serverBBotsOff = True
            await ctx.interaction.response.send_message("Mom and Dad are now muted. Their messages will be deleted if "
                                                        "not sent in their respective channels.")
#END [ServerB Commands]

bot.run('[REDACTED]')