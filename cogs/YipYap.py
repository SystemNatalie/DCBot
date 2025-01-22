from datetime import datetime

from discord.ext import commands
import asyncio
from StateManager import StateManager, CharacterNotFound
import random
random.seed()

class YipYap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.characterCache = {}

    async def cog_check(self, ctx):
        return ctx.author in self.bot.serverA.members
    #todo update character cache info if addupdatecharacter
    #todo add character aliases
    @commands.hybrid_command()
    async def reroll(self,ctx):
        random_character = self.bot.sm.getRandomCharacter()
        oldCharacter = self.bot.sm.getCurrentCharacter(ctx.author.id)
        if oldCharacter is None:
            self.bot.sm.setUserInitialCharacter(ctx.author.id,random_character)
        else:
            self.bot.sm.updateUserCharacter(ctx.author.id,random_character,oldCharacter)
        self.characterCache[ctx.author.id] = random_character
        await ctx.reply("Rerolled successfully", ephemeral=True)

    @commands.hybrid_command()
    async def showroll(self, ctx):
        random_character = self.bot.sm.getRandomCharacter()
        oldCharacter = self.bot.sm.getCurrentCharacter(ctx.author.id)
        if oldCharacter is None:
            self.bot.sm.setUserInitialCharacter(ctx.author.id,random_character)
        else:
            self.bot.sm.updateUserCharacter(ctx.author.id,random_character,oldCharacter)
        self.characterCache[ctx.author.id] = random_character
        await ctx.reply(f"Rerolled to \"{random_character['name']}\" successfully", ephemeral=True)

    @commands.hybrid_command()
    async def beme(self, ctx):
        print(ctx.author.id)
        me = self.bot.sm.getMyCharacter(ctx.author.id)
        print(me)
        oldCharacter = self.bot.sm.getCurrentCharacter(ctx.author.id)
        if oldCharacter is None:
            self.bot.sm.setUserInitialCharacter(ctx.author.id,me)
        else:
            self.bot.sm.updateUserCharacter(ctx.author.id,me,oldCharacter)
        self.characterCache[ctx.author.id] = me
        await ctx.reply(f"Real Identity Active", ephemeral=True)

    #todo add god override to either claim character, or temporarily use the same character as someone else
    @commands.hybrid_command()
    async def selectcharacter(self, ctx, *, character_name):
        try:
            selected_character = self.bot.sm.getSpecificCharacter(character_name)
        except CharacterNotFound:
            #todo differentiate the two?
            await ctx.reply(f"Character not found or not authorized", ephemeral=True)
            return
        print(selected_character)
        if selected_character['cur_user'] is None:
            oldCharacter = self.bot.sm.getCurrentCharacter(ctx.author.id)
            if oldCharacter is None:
                self.bot.sm.setUserInitialCharacter(ctx.author.id, selected_character)
            else:
                self.bot.sm.updateUserCharacter(ctx.author.id, selected_character, oldCharacter)
            self.characterCache[ctx.author.id] = selected_character
            await ctx.reply(f"Selected \"{selected_character['name']}\" successfully", ephemeral=True)
        else:
            await ctx.reply(f"Character in use", ephemeral=True)

    @commands.hybrid_command()
    async def addupdatecharacter(self, ctx, *, character_name, avatar_url):
        self.bot.sm.upsertCharacter(character_name, avatar_url)
        await ctx.reply(f"Character added", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:                                                                                 # Ignore messages sent by self (the bot) #TODO unsure if necessary
            return
        if message.channel in self.bot.yipyapCategory.channels and not message.webhook_id:
            if message.author.id in self.characterCache:
                currentCharacter = self.characterCache[message.author.id]
            else:  # cache miss
                currentCharacter = self.bot.sm.getCurrentCharacter(message.author.id)
                if currentCharacter is None:
                    currentCharacter = self.bot.sm.getRandomCharacter()
                    self.bot.sm.setUserInitialCharacter(message.author.id, currentCharacter)
                self.characterCache[message.author.id] = currentCharacter
            loop = asyncio.get_event_loop() #todo do every time?
            for webhook in self.bot.yipyapWebhooks:  # intentionally not awaiting ? may cause doubling up rarely
                loop.create_task((webhook.send(content=message.content,
                                               embeds=message.embeds,
                                               files=[await attch.to_file() for attch in message.attachments],
                                               username=currentCharacter['name'], avatar_url=currentCharacter['avatar_url'], )))

            await message.delete()  # todo sometimes this is missed???

async def setup(bot):
    await bot.add_cog(YipYap(bot))