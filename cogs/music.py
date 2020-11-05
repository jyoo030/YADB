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
        self._queue = []
        self._loop = asyncio.get_event_loop()
        self.set_save_path()


    def set_save_path(self):
        self._SAVE_PATH = os.path.join(os.getcwd(), "Music")
        if not os.path.exists(self._SAVE_PATH):
            os.makedirs(self._SAVE_PATH)

    @commands.command(name="play", help="plays a song from youtube",)
    async def music_player(self, ctx, *, song_name):
        def play_next(ctx, old_song):
            if os.path.exists(old_song):
                os.remove(old_song)
            else:
                print("Error deleting recently played song")

            voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
            if len(self._queue) > 0:
                song = self._queue.pop(0)
                voice_client.play(discord.FFmpegPCMAudio(song.mp3), after=lambda e: play_next(ctx, song.mp3))
            else:
                asyncio.run_coroutine_threadsafe(voice_client.disconnect(), self._loop)

        voice_client = await self.join_vc_bot(ctx)

        try:
            song = await self._loop.run_in_executor(None, YoutubeDownloader().download, song_name, self._SAVE_PATH)
        except Exception as err:
            print(err)
            await ctx.send("the music player is still in alpha and crashes sometimes, please try again.")

        if not voice_client.is_playing():
            await ctx.send(f"Now Playing: {song.title}")
            voice_client.play(discord.FFmpegPCMAudio(song.mp3), after=lambda e: play_next(ctx, song.mp3))
            voice_client.volume = 100
            voice_client.is_playing()
        else:
            self._queue.append(song)
            await ctx.send(f"queued {song_name}")

    @music_player.error
    async def music_player_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send("You need to put a song name dummy!")
        else:
            print(error)
    
    @commands.command(name="queue", help="displays music queue")
    async def show_queue(self, ctx):
        if len(self._queue) == 0:
            await ctx.send("the queue is currently empty. try adding a song with !play <song_name>")
        else: 
            output = "the current queue is: \n"
            for index, song in enumerate(self._queue):
                output += f"{index + 1}): {song.title}\n"

            await ctx.send(output)

    @commands.command(name="leave", help="makes the bot leave your voice channel")
    async def leave_vc_bot(self, ctx):
        for vc in self.bot.voice_clients:
            if vc.guild == ctx.guild:
                await vc.disconnect()
                print(f"Disconnected from vc in: {ctx.guild}")
                return
        await ctx.send("I don't think I'm in a voice channel.")

    @commands.command(name="join", help="makes the bot join your voice channel")
    async def join_vc_bot(self, ctx):
        if not ctx.author.voice:
            await ctx.send("I can't play a song if you're not in a voice channel")
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
