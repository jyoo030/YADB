import asyncio
from collections import defaultdict

import discord
from discord.embeds import Embed
from discord.ext import commands
from discord.utils import get

from utilities.youtube_scraper import search_youtube, Song


class MusicListener:
    def __init__(self):
        self.queue = []
        self.queue_lock = asyncio.Lock()
        self.playing = None


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.guild_list["music"] = defaultdict(MusicListener)
        self.music_listeners = self.bot.guild_list["music"]

    @commands.command(name="play", help="plays a song from youtube")
    async def instant_play(self, ctx, *, song_name):
        if not await self.can_play_song(ctx):
            return

        music_listener = self.music_listeners[ctx.guild.id]

        # To avoid a race condition, we must secure a spot in the queue as soon as a user has requested it
        # this can be done at the same time as actually searching for a song to play
        _, search_results = await asyncio.gather(music_listener.queue_lock.acquire(), search_youtube(song_name, 1))
        if not search_results:
            await ctx.send(f"Sorry, unable to find any good matches for the song '{song_name}'.")
            music_listener.queue_lock.release()
            return

        song = search_results[0]
        song.requester = ctx.author.display_name
        song.avatar_url = str(ctx.author.avatar_url)
        music_listener.queue.append(song)
        music_listener.queue_lock.release()
        if music_listener.playing or not await self.start_playing(ctx):
            embed_fields = {
                'color': discord.Color.dark_gray().value,
                'title': 'Queued:',
                'description': f'[{song.title}](https://youtube.com{song.video_url}) [{song.length}]',
                'fields': [{
                    'name': 'Position',
                    'value': len(music_listener.queue)
                }],
                'thumbnail': {'url': song.thumbnail}
            }
            await ctx.send(embed=discord.Embed.from_dict(embed_fields))

    # a list of 1-10 emojis that a user in discord can select to choose their song
    SELECTION_REACTS = [f'{i}\N{combining enclosing keycap}' for i in range(1, 10)] + ['\N{Keycap Ten}']
    REACTION_TIMEOUT=30.0
    @commands.command(name="search", help="display and choose song from search")
    async def search_play(self, ctx, *, song_name):
        if not await self.can_play_song(ctx):
            return

        search_results = await search_youtube(song_name, 10)
        if not search_results:
            await ctx.send(f"Sorry, unable to find any good matches for the song '{song_name}'.")
            return

        formatted_search = '\n'.join([f"{index + 1}): [{song.title}](https://youtube.com{song.video_url}) [{song.length}]\n" for index, song in enumerate(search_results)])
        embed_fields = {
            'color': discord.Color.dark_gray().value,
            'title': f"Search results for : ```{song_name}```",
            'description': formatted_search,
            'fields':  [{
                'name': "Click on the number you want to play, or click the X to cancel",
                'value': "Note: search will auto-cancel after 30 seconds"
            }]
        }
        results_message = await ctx.send(embed=discord.Embed().from_dict(embed_fields))

        reactions_subset = MusicPlayer.SELECTION_REACTS[:len(search_results)] + ['\N{CROSS MARK}']
        async def send_reactions():
            for emoji in reactions_subset:
                await results_message.add_reaction(emoji)

        try:
            # We want the user to be able to react even before all the reactions have been sent, so we send them concurrenlty while waiting for a response
            verify_response = lambda reaction, user: user == ctx.author and reaction.emoji in reactions_subset
            _, (user_reaction, _) = await asyncio.gather(send_reactions(), self.bot.wait_for('reaction_add', timeout=MusicPlayer.REACTION_TIMEOUT, check=verify_response))
        except asyncio.TimeoutError:
            await ctx.send(f"You haven't made a valid selection for {MusicPlayer.REACTION_TIMEOUT} seconds, so the search has been cancelled.")
            return

        if user_reaction.emoji == '\N{CROSS MARK}':
            await ctx.send("Search cancelled")
            return

        song = search_results[reactions_subset.index(user_reaction.emoji)]
        song.requester = ctx.author.display_name
        song.avatar_url = str(ctx.author.avatar_url)
        music_listener = self.music_listeners[ctx.guild.id]
        await music_listener.queue_lock.acquire()
        music_listener.queue.append(song)
        music_listener.queue_lock.release()
        if music_listener.playing or not await self.start_playing(ctx):
            embed_fields = {
                'color': discord.Color.dark_gray().value,
                'title': 'Queued:',
                'description': f'[{song.title}](https://youtube.com{song.video_url}) [{song.length}]',
                'fields': [{
                    'name': 'Position',
                    'value': len(music_listener.queue)
                }],
                'thumbnail': {'url': song.thumbnail}
            }
            await ctx.send(embed=discord.Embed.from_dict(embed_fields))

    @commands.command(name="queue", help="displays music queue")
    async def show_queue(self, ctx):
        music_queue = self.music_listeners[ctx.guild.id].queue
        if len(music_queue) == 0:
            await ctx.send("The queue is currently empty. Try adding a song with !play <song_name>.")
        else:
            formatted_queue = '\n'.join([f"{index + 1}): [{song.title}](https://youtube.com{song.video_url}) [{song.length}] | {song.requester}" for index, song in enumerate(music_queue)])
            embed_fields = {
                'color': discord.Color.dark_gray().value,
                'title': 'Current Queue:',
                'description': formatted_queue
            }
            await ctx.send(embed=discord.Embed.from_dict(embed_fields))

    @commands.command(name="song", help="displays currently playing song")
    async def display_song(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        music_listener = self.music_listeners[ctx.guild.id]
        if music_listener.playing and voice_client and voice_client.is_connected():
            embed_fields = {
                'color': discord.Color.blue().value,
                'fields': [{
                    'name': 'Currently Playing:',
                    'value': f"[{music_listener.playing.title}](https://youtube.com{music_listener.playing.video_url}) [{music_listener.playing.length}]"
                }],
                'author': {
                    'name': music_listener.playing.requester,
                    'icon_url': music_listener.playing.avatar_url
                },
                'thumbnail': {'url': music_listener.playing.thumbnail}
            }
            await ctx.send(embed=discord.Embed.from_dict(embed_fields))
        else:
            await ctx.send("There is no song currently playing.")

    @commands.command(name="skip", help="Skips currently playing song")
    async def skip_song(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected() and self.music_listeners[ctx.guild.id].playing:
            # Stops current song from playing and triggers self.play_next
            voice_client.stop()
        else:
            await ctx.send("No song currently playing. Use !leave to boot the bot from the voice channel.")

    @commands.command(name="leave", help="makes the bot leave your voice channel")
    async def leave_voice_channel(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            self.music_listeners[ctx.guild.id].playing = None
            self.music_listeners[ctx.guild.id].queue.clear()
            await voice_client.disconnect()
            print(f"Disconnected from voice channel in: {ctx.guild}")
        else:
            await ctx.send("I don't think I'm in a voice channel.")

    @commands.command(name="join", help="makes the bot join your voice channel")
    async def join_voice_channel(self, ctx):
        if not ctx.author.voice:
            await ctx.send("I can't join if you're not in a voice channel!")
            return None

        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if not voice_client or not voice_client.is_connected():
            return await ctx.author.voice.channel.connect()
        elif voice_client.channel != ctx.author.voice.channel:
            await voice_client.move_to(ctx.author.voice.channel)
        elif ctx.command.name == "join":
            await ctx.send("I'm already in your channel!")
        return voice_client

    @commands.command(name="volume", help="adjust the volume of the bot, from 0-200")
    async def adjust_vol(self, ctx, volume: float):
        volume /= 100
        if not (0 <= volume <= 2):
            await ctx.send("send a number between 0 and 200 for volume!")
            return

        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            await ctx.send("Can't adjust volume if nothing is playing.")
        elif isinstance(voice_client.source, discord.player.PCMVolumeTransformer):
            voice_client.source.volume = volume
        else:
            voice_client.source = discord.PCMVolumeTransformer(voice_client.source, volume=volume)

    @commands.command(name="pause", help="Pauses music player")
    async def pause(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected() and not voice_client.is_paused():
            voice_client.pause()
        else:
            await ctx.send("Music Player already isn't playing.")

    @commands.command(name="resume", help="Resumes paused playback")
    async def resume(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if not voice_client or not voice_client.is_connected():
            await ctx.send("Can't resume what hasn't been paused.")
            return

        if voice_client.is_paused():
            voice_client.resume()
        else:
            await self.start_playing(ctx)

    @commands.command(name="remove", help="Removes x position song from the queue")
    async def remove(self, ctx, song_pos: int):
        music_queue = self.music_listeners[ctx.guild.id].queue

        if len(music_queue) == 0:
            await ctx.send("The queue is already empty. There is nothing to remove.")
        elif not (1 <= song_pos <= len(music_queue)):
            await ctx.send("Invalid song position. Please try again.")
        else:
            music_queue.pop(song_pos - 1)


    #region Non-Command Functions
    async def can_play_song(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel to play music.")
            return False
        elif voice_client and ctx.author.voice.channel != voice_client.channel:
            await ctx.send("Sorry, music is already playing in a different channel.")
            return False
        return True

    # Options needed for the audio stream to not cutoff towards the end
    # https://stackoverflow.com/questions/61959495/when-playing-audio-the-last-part-is-cut-off-how-can-this-be-fixed-discord-py
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    async def start_playing(self, ctx):
        voice_client = await self.join_voice_channel(ctx)
        if not voice_client:
            return False

        music_listener = self.music_listeners[ctx.guild.id]
        music_listener.playing = music_listener.queue.pop(0)

        loop = asyncio.get_event_loop()
        play_next = lambda error: asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop)
        voice_client.play(discord.FFmpegPCMAudio(music_listener.playing.audio_url, **MusicPlayer.FFMPEG_OPTIONS), after=play_next)
        embed_fields = {
            'color': discord.Color.blue().value,
            'fields': [{
                'name': 'Now Playing:',
                'value': f"[{music_listener.playing.title}](https://youtube.com{music_listener.playing.video_url}) [{music_listener.playing.length}]"
            }],
            'author': {
                'name': music_listener.playing.requester,
                'icon_url': music_listener.playing.avatar_url
            },
            'thumbnail': {'url': music_listener.playing.thumbnail}
        }
        await ctx.send(embed=discord.Embed.from_dict(embed_fields))
        return True

    async def play_next(self, ctx):
        music_listener = self.music_listeners[ctx.guild.id]
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if len(music_listener.queue) == 0:
            music_listener.playing = None
            await voice_client.disconnect()
        else:
            await self.start_playing(ctx)
    #endregion


def setup(bot):
    bot.add_cog(MusicPlayer(bot))
