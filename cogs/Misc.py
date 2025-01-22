from discord.ext import commands
import discord
class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return True #ctx.author.id == 909958405161119824

    @commands.Cog.listener(name="on_message")
    async def mentioncrossover(self, message):
        if message.author == self.bot.user:                                                                                 # Ignore messages sent by self (the bot) #TODO unsure if necessary
            return
        if message.guild == self.bot.serverA:
            # todo dont mention on @ everyone or on shared roles?
            god = message.guild.get_member(909958405161119824)
            fae = message.guild.get_member(1176418273458401313)
            mentioned = False
            if fae.mentioned_in(message) and not mentioned:
                mentioned = True
                await message.channel.send(f'<@!{909958405161119824}>')
            elif god.mentioned_in(message) and not mentioned:
                mentioned = True
                await message.channel.send(f'<@!{1176418273458401313}>')
            if message.type == discord.MessageType.reply:
                originalMessage = await message.channel.fetch_message(message.reference.message_id)
                if originalMessage.author == fae and not mentioned:
                    mentioned = True
                    await message.channel.send(f'<@!{909958405161119824}>')
                elif originalMessage.author == god and not mentioned:
                    mentioned = True
                    await message.channel.send(f'<@!{1176418273458401313}>')

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def pinitadd(self, payload):
        # PIN-IT add functionality.
        # Pins a message if there is one or more "📌" reaction added.
        # Allows pinning as a group and without perms
        if payload.emoji.name == '📌':
            msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            for reaction in msg.reactions:
                if reaction.emoji == '📌' and reaction.count == 1:  # Only pin on the first instance of getting the reaction. No need to waste calls.
                    try:
                        await msg.pin()
                        return
                    except Exception as e:  # TODO
                        print("Exception")

    @commands.Cog.listener(name="on_raw_reaction_remove")
    async def pinitremove(self, payload):
        # PIN-IT remove functionality.
        # Un-pins a message if there are 0 "📌" reactions after a reaction removal.
        if payload.emoji.name == '📌':
            msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            for reaction in msg.reactions:
                if reaction.emoji == '📌':  # If we see even one pin, it's still pinned, so we can just quit after seeing a pin.
                    return
            try:  # We only hit this if we never see a pin
                await msg.unpin()
            except Exception as e:
                print("Exception")  # TODO
            return

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def remindmeadd(self, payload):
        if payload.emoji.name == '⏰':
            msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            self.bot.sm.addRemindeeFromMessageID(payload.user_id, msg.id)

    @commands.Cog.listener(name="on_raw_reaction_remove")
    async def remindmeremove(self, payload):
        if payload.emoji.name == '⏰':
            msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            self.bot.sm.remove_remindee_from_message_id(payload.user_id, msg.id)



async def setup(bot):
    await bot.add_cog(Misc(bot))