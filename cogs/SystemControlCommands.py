#todo redo all this
import discord
from discord.ext import commands, tasks

#FUCKED CODE START
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from utils import stringToSeconds
import asyncio
from typing import Optional
from discord.ext import commands, tasks
import win32gui
import win32con

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



class SystemControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.id == 909958405161119824

    @commands.hybrid_command()
    async def sleeptimer(self, ctx, *, countdowntime: Optional[str]):  # Turns off my pc screen
        SC_MONITORPOWER = 0xF170
        if countdowntime:  # TODO support float inputs
            foundGroup, waitTime = stringToSeconds(countdowntime)
            if foundGroup:
                await ctx.reply("Sleep timer active", ephemeral=True)
                await asyncio.sleep(waitTime)  # TODO understand why non-blocking is important
                win32gui.SendMessageTimeout(win32con.HWND_BROADCAST,
                                            win32con.WM_SYSCOMMAND,
                                            SC_MONITORPOWER, 2,
                                            win32con.SMTO_NOTIMEOUTIFNOTHUNG,
                                            1000)
            else:
                await ctx.reply("error no groups found", ephemeral=True)
        else:
            win32gui.SendMessageTimeout(win32con.HWND_BROADCAST,
                                        win32con.WM_SYSCOMMAND,
                                        SC_MONITORPOWER, 2,
                                        win32con.SMTO_NOTIMEOUTIFNOTHUNG,
                                        1000)
            await ctx.reply("Sleep Active", ephemeral=True)

    @commands.hybrid_command()
    async def setvolume(self, ctx, *, volume: str):  # Turns off my pc screen
        #TODO make this use buttons instead of this being a command
        try:
            set_volume(float(volume))
            await ctx.reply("done", ephemeral=True)
        except:
            await ctx.reply("error", ephemeral=True)
async def setup(bot):
    await bot.add_cog(SystemControl(bot))