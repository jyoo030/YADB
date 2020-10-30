import os, sys
import asyncio

import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utilities.scraper import YoutubeDownloader


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="play",
        help="!play <song name> to play a song in your current voice channel from Youtube.",
    )
    async def music_player(self, ctx, *, arg):
        SAVE_PATH = os.path.join(os.getcwd(), "Music")
        if not os.path.exists(SAVE_PATH):
            os.makedirs(SAVE_PATH)

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, YoutubeDownloader().download, arg, SAVE_PATH)
        except:
            ctx.send("the music player is still in alpha and crashes sometimes, please try again.")

        for file in os.listdir(SAVE_PATH):
            if file.endswith(".mp3"):
                song = file

        await ctx.send("Playing song now.")
        voice_client = await self.join_vc_bot(ctx)
        if voice_client:
            await ctx.send("Playing song now.")
            voice_client.play(discord.FFmpegPCMAudio(song))
            voice_client.volume = 100
            voice_client.is_playing()

    @music_player.error
    async def music_player_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send("You need to put a song name dummy!")
        else:
            print(error)

    @commands.command(name="leave", help="Makes the bot leave your voice channel.")
    @commands.is_owner()
    async def leave_vc_bot(self, ctx):
        for vc in self.bot.voice_clients:
            if vc.guild == ctx.guild:
                await vc.disconnect()
                print(f"Disconnected from vc in: {ctx.guild}")
                return
        await ctx.send("I don't think I'm in a voice channel.")

    @commands.command(
        name="join", help="[ADMIN ONLY] Makes the bot join your current voice channel."
    )
    async def join_vc_bot(self, ctx):
        if not ctx.author.voice:
            await ctx.send(
                "Hey man, I can't play a song if you're not in a voice channel"
            )
            return

        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            await voice_client.move_to(ctx.author.voice.channel)
        else:
            user_vc = ctx.author.voice.channel
            voice_client = await user_vc.connect()
            print(f"The bot has connected to {user_vc}")
        return voice_client


def setup(bot):
    bot.add_cog(MusicPlayer(bot))
