from discord.ext import commands
import discord
class Whiteboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return True #ctx.author.id == 909958405161119824





async def setup(bot):
    await bot.add_cog(Misc(bot))