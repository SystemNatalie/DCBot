from discord.ext import commands
import discord


class DevelopmentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    @commands.hybrid_command()
    async def syncglobal(self,ctx):
            await self.bot.tree.sync()
            await ctx.send('Commands synced globally')

    @commands.hybrid_command()
    async def sync(self,ctx):  # Todo make this sync to the server im sending this from?
            self.bot.tree.clear_commands(guild=discord.Object(id=ctx.guild.id))
            # bot.tree.copy_global_to(guild=discord.Object(id =ctx.guild.id))
            await self.bot.tree.sync(guild=discord.Object(id=ctx.guild.id))
            await ctx.send('Commands synced to this server')


async def setup(bot):
    await bot.add_cog(DevelopmentCommands(bot))


