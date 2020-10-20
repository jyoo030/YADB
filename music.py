import os
from os import system
from urllib.parse import urlparse

import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl
from discord import FFmpegPCMAudio

class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='play', help='!play <song name> to play a song in your current voice channel from Youtube.')
    async def music_player(self, ctx, *, arg):
        self.join_vc_bot(ctx)

        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            await ctx.send("Wait for the current playing music end or use the 'stop' command")
            return

        await ctx.send("Getting everything ready, playing audio soon")
        print("Someone wants to play music let me get that ready for them...")
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([arg])
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, 'song.mp3')
        voice.play(discord.FFmpegPCMAudio("song.mp3"))
        voice.volume = 100
        voice.is_playing()

    @commands.command(name='leave', help='Makes the bot leave your voice channel.')
    @commands.is_owner()
    async def leave_vc_bot(self, ctx):
        for vc in self.bot.voice_clients:
            if vc.guild == ctx.guild:
                await vc.disconnect()
                return
        await ctx.send("I don't think I'm in a voice channel.")
    
    @commands.command(name='join', help='Makes the bot join your current voice channel.')
    async def join_vc_bot(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            await voice_client.move_to(ctx.author.voice.channel)
        else:
            user_channel = ctx.author.voice.channel
            await user_channel.connect()

    @music_player.error
    async def music_player_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send("You need to put a song name dummy!")
        else:
            print(error)

def setup(bot):
    bot.add_cog(MusicPlayer(bot))
