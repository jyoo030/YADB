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
        self._loop = asyncio.get_event_loop()
        self._selection_reacts = ['1\N{combining enclosing keycap}', 
                            '2\N{combining enclosing keycap}', 
                            '3\N{combining enclosing keycap}', 
                            '4\N{combining enclosing keycap}', 
                            '5\N{combining enclosing keycap}', 
                            '6\N{combining enclosing keycap}', 
                            '7\N{combining enclosing keycap}', 
                            '8\N{combining enclosing keycap}', 
                            '9\N{combining enclosing keycap}', 
                            '\N{Keycap Ten}']
        self.__set_save_path()

    def __set_save_path(self):
        self._BASE_SAVE_PATH = os.path.join(os.getcwd(), "Music")
        self.__path_exists(self._BASE_SAVE_PATH)
    
    def __path_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @commands.command(name="play", help="plays a song from youtube")
    async def instant_play(self, ctx, *, song_name):
        song_select = await self._loop.run_in_executor(None, YoutubeDownloader().solo_search, song_name, self.__path_exists(os.path.join(self._BASE_SAVE_PATH, str(ctx.guild.id))))

        try:
            song = await self._loop.run_in_executor(None, YoutubeDownloader().download, song_select)
        except Exception as err:
            await ctx.send("the music player is still in alpha and crashes sometimes, please try again.")
            raise err

        await self.__play_song(ctx, song)
    
    @instant_play.error
    async def instant_play_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send("You need to put a song name dummy!")
        else:
            print(error)

    async def __play_song(self, ctx, song):
        voice_client = await self.join_vc_bot(ctx)
        if not voice_client.is_playing():
            self.bot.guild_list[ctx.guild.id]['curr_song'] = song
            await ctx.send(f"Now Playing: {song.title}")
            voice_client.play(discord.FFmpegPCMAudio(song.mp3), after=lambda e: self.__play_next(ctx, song.mp3))
            voice_client.volume = 100
            voice_client.is_playing()
        else:
            self.bot.guild_list[ctx.guild.id]["queue"].append(song)
            await ctx.send(f"Queued {song.title}")

    def __play_next(self, ctx, old_song):
        if os.path.exists(old_song):
            os.remove(old_song)
        else:
            print(f"Error deleting recently played song {old_song}")

        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            return
        elif len(self.bot.guild_list[ctx.guild.id]["queue"]) > 0:
            song = self.bot.guild_list[ctx.guild.id]["queue"].pop(0)
            self.bot.guild_list[ctx.guild.id]["curr_song"] = song
            voice_client.play(discord.FFmpegPCMAudio(song.mp3), after=lambda e: self.__play_next(ctx, song.mp3))
        else:
            asyncio.run_coroutine_threadsafe(voice_client.disconnect(), self._loop)
    
    @commands.command(name="search", help="display and choose song from search")
    async def search_play(self, ctx, *, song_name):
        def __search_reply_valid(reaction, user):
            return user == ctx.author and reaction.emoji in self._selection_reacts
        results = await self._loop.run_in_executor(None, YoutubeDownloader().multi_search, song_name, self.__path_exists(os.path.join(self._BASE_SAVE_PATH, str(ctx.guild.id))))

        output = f"Search Results for: {song_name}\n"
        for index, result in enumerate(results):
            output += f"{index+1}): {result.title}\n"
        output += "\n Click on the number you want to play."
        output += "\n Please wait for buttons 1-10 to load before selecting"

        result_msg = await ctx.send(output)

        for i in range(len(results)):
            await result_msg.add_reaction(self._selection_reacts[i])
        
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=15.0, check=__search_reply_valid)
        except asyncio.TimeoutError:
            await ctx.send("You haven't made a valid selection for 15 seconds, or selected too early, so the search has been cancelled.")

        song_select = results[self._selection_reacts.index(reaction.emoji)]
        try:
            song = await self._loop.run_in_executor(None, YoutubeDownloader().download, song_select)
        except Exception as err:
            await ctx.send("the music player is still in alpha and crashes sometimes, please try again.")
            raise err

        await self.__play_song(ctx, song)

    @search_play.error
    async def search_play_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send("You need to put a song name dummy!")
        else:
            print(error)

    @commands.command(name="queue", help="displays music queue")
    async def show_queue(self, ctx):
        if len(self.bot.guild_list[ctx.guild.id]["queue"]) == 0:
            await ctx.send("the queue is currently empty. try adding a song with !play <song_name>")
        else: 
            output = "the current queue is: \n"
            for index, song in enumerate(self.bot.guild_list[ctx.guild.id]["queue"]):
                output += f"{index + 1}): {song.title}\n"

            await ctx.send(output)
    
    @commands.command(name="song", help="displays currently playing song")
    async def display_song(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            await ctx.send(f"The currently playing song is: {self.bot.guild_list[ctx.guild.id]['curr_song'].title}")
        else:
            await ctx.send("There is no song currently playing.")

    @commands.command(name="skip", help="Skips currently playing song")
    async def skip_song(self, ctx):
        if len(self.bot.guild_list[ctx.guild.id]['queue']) == 0:
            await ctx.send("The queue is empty; No song to skip to. Use !leave to boot the bot from the voice channel")
        else:
            voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
            if voice_client and voice_client.is_connected():
                #FIXME: Console gives deletion error but deletes file anyways. play_next called twice perhaps? or a race condition?
                voice_client.stop()
                self.__play_next(ctx, self.bot.guild_list[ctx.guild.id]['curr_song'].mp3)

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

    @commands.command(name="volume", help="adjust the volume of the bot")
    async def adjust_vol(self, ctx, volume):
        try:
            volume = float(volume)/100
        except ValueError:
            await ctx.send("send a number between 0 and 200 for volume!")
            return

        vc = get(ctx.bot.voice_clients, guild=ctx.guild)
        if volume < 0 or volume > 2.0:
            await ctx.send("please send an value from 0-200")
        elif not vc:
            await ctx.send("can't adjust volume if nothing is playing")
        else:
            if isinstance(vc.source, discord.player.PCMVolumeTransformer):
                vc.source.volume = volume
            else:
                vc.source = discord.PCMVolumeTransformer(vc.source, volume=volume)


def setup(bot):
    bot.add_cog(MusicPlayer(bot))
