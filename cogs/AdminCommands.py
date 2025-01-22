from discord.ext import commands
import asyncio
from utils import chunks

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    @commands.hybrid_command()
    async def manualpurge(self,ctx):  # TODO would it be easier to just delete a channel and recreate it instead of wiping each message?
            messagesToDelete = []
            async for message in ctx.channel.history(oldest_first=True, limit=None):
                messagesToDelete.append(message)
            for chunk in chunks(messagesToDelete, 100):
                try:
                    await ctx.channel.delete_messages(chunk)
                # TODO test all cases (15days old, etc)
                except Exception as e:  # If we hit an exception, try to manually delete the messages one-by-one
                    for message in chunk:
                        await message.delete()
                        await asyncio.sleep(0.5)
                        # Rate limit
            await ctx.channel.send('Chat Purged.')

    @commands.hybrid_command()
    async def selfdestruct(self,ctx):  # Leaves all guilds
            if self.bot.selfDestructSaftey:
                for guild in self.bot.guilds:
                    await guild.leave()
            else:
                self.bot.selfDestructSaftey = True
                await ctx.reply("Safety off. Careful!")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))