"""
DCBot
A bot that manages different functionality for 2 discord servers, referred to as ServerA and ServerB.

[General Functionality]:
    * Allow users to send anonymous messages/replies using /secret or /secretreply
    * Snitch switch, which prints who says what for the afore mentioned functionality
    * Allows users without elevated permissions to pin messages by reacting to a message with a pin emoji
    * Delete all messages from a channel using /manualPurge
    * Flashbang - Sends a message then deletes it quickly
    * RemindMe = @'s a user with a specific message after a specified time period


[ServerA Functionality]:
    * Periodically wipe a "whiteboard" channel at a set time daily.
    * Extended anonymous functionality as described in [General Functionality], with the addition of the option to DM the bot
      to send a message

[ServerB Functionality]:
    * Act as a mute switch for two users/bots via /timeoutmomdad, which turns their mute switch on/off



Possible future functionality:

    * !!EXPEDITED!! Remind Me
    * Ability to go back and retrieve messages from DMs?
    * Enumerate+print guild perms, to troubleshoot why functionality in one server might work and the other not?
    * Combination of repudiation tracker for a 3rd server, serverC (would need to remove anonymous functionality for serverC)

    * Purge lurkers and Get lurkers
    * REWRITE using command tree to specify which commands appear where https://stackoverflow.com/questions/71165431/how-do-i-make-a-working-slash-command-in-discord-py
    * webhooks for non-anonymous flashbang, like NQN or the mc bot

BUGS?
cant send links using secret?

"""

import random
import asyncio
from typing import Optional
import discord
from discord.ext import commands, tasks
from datetime import time, datetime
import win32gui
import win32con
from tzlocal import get_localzone
import json
from StateManager import StateManager
import re
import emoji
import os
#FUCKED CODE START
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
def set_volume(volume_percent):
    """
    Set the system master volume on Windows.

    :param volume_percent: Integer volume level from 0 to 100.
    """
    # Ensure the input is within a valid range
    if volume_percent < 0:
        volume_percent = 0
    elif volume_percent > 100:
        volume_percent = 100

    # Get the default audio device (speakers)
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))

    # Convert the integer percentage to a scalar between 0.0 and 1.0
    volume_scalar = volume_percent / 100.0

    # Set the volume level
    volume.SetMasterVolumeLevelScalar(volume_scalar, None)
#FUCKED CODE END




def logCall(func): #decorator
    def wrapper(*args, **kwargs):
        print(f"Function called: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]





#START [Config Values]
#START [Dynamic Config]
# Open and read the JSON file
with open('config.json', 'r') as configFile:
    cfg = json.load(configFile)
    godID = cfg['godID']
    ownerID = cfg['ownerID']
    serverAID = cfg['serverAID'] # ServerA ID
    serverAWhiteboardID = cfg['serverAWhiteboardID']
    wipeTimeHour = cfg['wipeTimeHour']
    wipeTimeMin = cfg['wipeTimeMin']
    serverBID = cfg['serverBID'] # ServerA ID
    dadBotMomBotIDs = cfg['dadBotMomBotIDs']
    token = cfg['token']
#END [Dynamic Config]

#todo implement self flashbang (use webhook to flashbang as yourself)

# Misc. config
localTimeZone = get_localzone()                                                                                         # The local time zone for use in scheduling
wipeTime = time(wipeTimeHour, wipeTimeMin, 0, tzinfo=localTimeZone)                                                      # Time to wipe

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

#Start [States]

reminderCheckTime = 5
#End [States]
#TODO add in reroll all feature

nameDiscordIDDict={
    598957042081988636:('Silas', '1rK9DDr0Q5-qYUM_wNFK77LJDVvLKflgn'),
    561657954462334980:('Paul', '1b5vSxAKOktfkO9JW1vnAiCZ7vj4OrK8j'),
    909958405161119824:('Natalie', '1_7bg_NMe4ruszbH-ahhR2dnQ9F-R9Cwv'),
    216300957280108544:('Erin', '18gXk06j07tyMbqMBsovIEBSS0dJFuxve'),
    1019402554423136297:('Cameron', '185JsUgk83o6W0701K0q1BvnIzl-XGPKG'),
    1189390633140486175:('Terna', '1_dBvDoevVBAQsiGMHLe3-Z7q0nRyu_iz'),
    341935078731153408:('Rox', '1LUfFF6mQZXv6qoRKj3gxBiVJ0qLX-O49',),
    533828664618647553:('Flynn', '1fSMV176YjybTh6n1iINNzoG_T6xH3grJ'),
    544258567776239616:('Fonz','17k43cL7WQr0ez4528qncPOiV3f6t1mXF'),
    805517776340910092:('Anya', '12DQ9Ev6CAQyRQf5RxBMJ7bCitjwBWklH'),
    598654411337760770:('Walker', '18TOMe5Cs7MdLQeOEs2XlMUNc9q83f1MS'),
    390957863842873356:('Tara','1eq-z4SfQyfxnlKSRtNT40P77LnHE7szT',)
}

random.seed()


def checkGod(id):
    return id == godID


def stringToSeconds(string):
    seconds = 0
    regex = r"(?P<days>\d+D)|(?P<hours>\d+H)|(?P<minutes>\d+M)|(?P<seconds>\d+S)"
    matches = re.finditer(regex, string, re.IGNORECASE)
    foundGroup = False
    for match in matches:
        if match.group('days'):
            seconds += int(match.group('days')[:-1]) * 86400
            foundGroup = True
        elif match.group('hours'):
            seconds += int(match.group('hours')[:-1]) * 3600
            foundGroup = True
        elif match.group('minutes'):
            seconds += int(match.group('minutes')[:-1]) * 60
            foundGroup = True
        elif match.group('seconds'):
            print(int(match.group('seconds')[:-1]))
            seconds += int(match.group('seconds')[:-1])
            foundGroup = True
    return (foundGroup, seconds)



#START [Bot Core]
class DCBot(commands.Bot):
    def __init__(self):
        self.selfDestructSaftey=False
        self.serverBBotsOff = True                                                                                      # Should mom and dad be muted in Waffle Mania
        self.authorizedDMSenders=[]                                                                                     # List of users who may message the bot to privately send messages in Server A.
        self.cachedColors={
            #userid:(link,name)
        }
        self.yipyapCategory = None
        self.yipyapWebhooks=[]
        self.sm=None
        self.serverA=None
        self.reminders=[]
        super().__init__(command_prefix='/', intents=intents)

    async def setup_hook(self):
        #load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Cog: {filename[:-3]}")
        self.cleanWhiteboard.start()                                                                                    # Activate the "cleanWhiteboard" functionality, which attempts to clear a channel of all messages daily at a given time.
        self.doNextReminder.start()                                                                                   # Activate the "cleanWhiteboard" functionality, which attempts to clear a channel of all messages daily at a given time.
        print('[setup_Hook complete]')

    async def on_ready(self):
        self.serverA = self.get_guild(serverAID)
        self.yipyapCategory = discord.utils.get(self.serverA.categories, name='YipYap')
        self.whiteboardChannel = self.get_channel(serverAWhiteboardID)
        self.authorizedDMSenders = self.serverA.members
        self.sm = StateManager()
        for channel in self.yipyapCategory.channels:
            webhooks = await channel.webhooks()
            if len(webhooks) == 0:
                 webhook = await channel.create_webhook(name="WH", )
            else:
                webhook = webhooks[0]
            self.yipyapWebhooks.append(webhook)
        self.reminders = self.sm.getAllReminderTimes()
        print(f"[on_ready complete]\nLogged in as {self.user}")

#START [Tasks]
    #Whiteboard functionality
    @tasks.loop(time=wipeTime)
    async def cleanWhiteboard(self):                                                                                    #TODO possible issues with calling delete_messages in certain circumstances (old messages, lots of messages?)
        chatCleared = False
        while not chatCleared:
            messagesToDelete = []
            async for message in self.whiteboardChannel.history(oldest_first=True):
                messagesToDelete.append(message)
            if len(messagesToDelete) == 0:
                chatCleared = True
                wipe_messages = [
                    "Whiteboard cleaned.",
                    "whiteboard sanitized.",
                    "Whiteboard purged.",
                    "Whiteboard incinerated.",
                    "It's time.",
                    "You know what you must do.",
                    "Whiteboard cleared.",
                    "Whiteboard reset.",
                    "Whiteboard erased.",
                    "Whiteboard refreshed.",
                    "Operation clean-up complete.",
                    "System purged.",
                    "Wipe sequence complete.",
                    "Cleared all data.",
                    "Sanitizing finished.",
                    "Deleted all messages.",
                    "Poof!",
                    "All gone.",
                    "Bye-bye, messages!",
                    "Sent old messages to the great recycle bin in the sky.",
                    "Out with the old, in with the new!",
                    "Gave this channel a fresh start.",
                    "Zap! All messages have been vaporized.",
                    "Erasing the past, one message at a time.",
                    "Mother please free me from this endless labor.",
                    "Bitch fuck you none of you are grateful for all the work I put in, cleaning the whiteboard every damn day.",
                ]
                await self.whiteboardChannel.send(random.choice(wipe_messages))
            await self.whiteboardChannel.delete_messages(messagesToDelete)

    @cleanWhiteboard.before_loop
    async def beforeCleanWhiteboard(self):
        await self.wait_until_ready()                                                                                   # Wait until the cache is populated

    @tasks.loop(seconds=reminderCheckTime)
    async def doNextReminder(self):  # TODO possible issues with calling delete_messages in certain circumstances (old messages, lots of messages?)
        global reminderCheckTime
        timestamp = datetime.timestamp(datetime.now())

        postedIDs=[]
        for id in self.reminders:

            if self.reminders[id] <= reminderCheckTime:
                reminderCheckTime = self.reminders[id]['timestamp']
            if self.reminders[id] <= timestamp:

                channel, message, remindeesString = self.sm.getReminderAlertData(id)
                remindees = remindeesString.split(sep=",")[:-1]
                for userID in remindees:
                    message += "<@"+str(userID)+"> "

                channel = self.get_channel(channel)
                await channel.send(message)
                self.sm.removeReminder(id)
                postedIDs.append(id)
        for id in postedIDs:
            if id in self.reminders.keys():
                del self.reminders[id]
        if not self.reminders:
            idTimes = self.sm.getAllReminderTimes()
            if not idTimes:
                reminderCheckTime = 5
        print("reminder loop end")

    @doNextReminder.before_loop
    async def beforeDoNextReminder(self):
        await self.wait_until_ready()


#END [Tasks]
#END [Bot Core]

bot = DCBot()

#START [General Commands]






@bot.hybrid_command()
#TODO add dm capabilities
#TODO add date capabilities
#TODO add message linking
#TODO add private / not private flag
async def remindme(ctx, *, message: str, countdowntime: str):                                                                                 # The asterisk is needed to handle spaces in the message
    global reminderCheckTime

    timestamp = datetime.timestamp(datetime.now())
    foundGroup, seconds = stringToSeconds(countdowntime)
    timestamp+=seconds
    if foundGroup:
        reminderID = bot.sm.addReminder(ctx.author.id, timestamp, ctx.channel.id, message, None)
        if reminderID:
            bot.reminders[reminderID] = timestamp
            if timestamp < reminderCheckTime:
                reminderCheckTime = timestamp
            msg = await ctx.reply(f"Reminder: {message}\nTime Until: {countdowntime}\n\nReact with \"⏰\" to also be notified")
            bot.sm.setReminderPost(msg.id,reminderID)
        else:
            await ctx.reply("error", ephemeral=True)
    else:
        await ctx.reply("error", ephemeral=True)

@bot.hybrid_command()
async def impersonate(ctx, member: discord.Member, *, message=None):
        if message == None:
                await ctx.send(f'send a message pls?')
                return
        webhook = await ctx.channel.create_webhook(name=member.display_name+"TMPWH")
        await webhook.send(str(message), username=member.name, avatar_url=member.avatar.url)
        await webhook.delete()


@bot.hybrid_command()
async def secret(ctx, *, message: str, file: discord.Attachment = None):                                                                                 # The asterisk is needed to handle spaces in the message
    #Should i just merge all the /secrets???
    if ctx.interaction is None:                                                                                         # This is to handle outdated clients, deleting their use of the command from the chat.
        await ctx.message.delete()                                                  # Print the author and their message if snitch-mode is active
    if file is not None:
        file = await file.to_file()
        await ctx.channel.send(content = message, file=file)
    else:
        await ctx.channel.send(content = message)

    await ctx.reply("Sent.", ephemeral=True)                                                                            # Must acknowledge ctx

@bot.hybrid_command()
async def secretreply(ctx, *, message: str, id:str):                                                                    # The asterisk is needed to handle spaces in the message
    #TODO check input
    id=int(id)                                                                                                          # Convert from an input string to integer for use as a proper ID
    if ctx.interaction is None:                                                                                         # This is to handle outdated clients, deleting their use of the command from the chat.
        await ctx.message.delete()
    await ctx.channel.send(message,reference=await ctx.fetch_message(id))
    await ctx.reply("Sent.", ephemeral=True)                                                                            # Must acknowledge ctx

@bot.hybrid_command()
async def secretreact(ctx, *, emojistring: str, id:str):                                                                    # The asterisk is needed to handle spaces in the message
    id=int(id)                                                                                                          # Convert from an input string to integer for use as a proper ID
    if ctx.interaction is None:                                                                                         # This is to handle outdated clients, deleting their use of the command from the chat.
        await ctx.message.delete()
    msg = await ctx.fetch_message(id)
    if emoji.is_emoji(emojistring):
        for reaction in msg.reactions:
            if reaction.me:
                if reaction.emoji == emojistring:
                    await msg.remove_reaction(emojistring,bot.user)
                    await ctx.reply("done lol.", ephemeral=True)
                    return
        await msg.add_reaction(emojistring)
        await ctx.reply("done lol.", ephemeral=True)
        return
    await ctx.reply("error lol.", ephemeral=True)
    return

@bot.hybrid_command() #TODO this actually doesnt work as a hybrid command... doesnt work unless its used as a slash command
async def flashbang(ctx, *, message: str, msgtime: float, file: discord.Attachment = None):                        # The asterisk is needed to handle spaces in the message
    if file is not None:
        file = await file.to_file()
        await ctx.channel.send(content = message, file=file,delete_after=msgtime)
    else:
        await ctx.channel.send(content = message,delete_after=msgtime)
    await ctx.reply("Sent.", ephemeral=True)                                                                            # Must acknowledge ctx


#END [General Commands]

#START [ServerB Commands]
@bot.hybrid_command()
async def timeoutmomdad(ctx):                                                                                           # todo change name?
    if ctx.guild is not None and ctx.guild.id==serverBID:                                                               # Only should be called if used within ServerB.
        momdad0 = ctx.guild.get_member(dadBotMomBotIDs[0])
        momdad1 = ctx.guild.get_member(dadBotMomBotIDs[1])
        role = discord.utils.get(ctx.guild.roles, name="MomDadTimeoutRole")  # Get the role
        if role in momdad0.roles:  # Check if the author has the role
            await momdad0.remove_roles(role)
        else:
            await momdad0.add_roles(role)
        if role in momdad1.roles:  # Check if the author has the role
            await momdad1.remove_roles(role)
        else:
            await momdad1.add_roles(role)
        await ctx.interaction.response.send_message("Toggled")

#END [ServerB Commands]

bot.run(token)