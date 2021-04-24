import asyncio
from collections import defaultdict

import discord
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
        music_listener = self.music_listeners[ctx.guild.id]

        # To avoid a race condition, we must secure a spot in the queue as soon as a user has requested it
        # this can be done at the same time as actually searching for a song to play
        _, search_results = await asyncio.gather(music_listener.queue_lock.acquire(), search_youtube(song_name, 1))
        if not search_results:
            await ctx.send(f"Sorry, unable to find any good matches for the song '{song_name}'.")
            music_listener.queue_lock.release()
            return

        song = search_results[0]
        music_listener.queue.append(song)
        music_listener.queue_lock.release()
        if music_listener.playing or not await self.start_playing(ctx):
            await ctx.send(f"Queued {song.title}")

    # a list of 1-10 emojis that a user in discord can select to choose their song
    SELECTION_REACTS = [f'{i}\N{combining enclosing keycap}' for i in range(1, 10)] + ['\N{Keycap Ten}']
    @commands.command(name="search", help="display and choose song from search")
    async def search_play(self, ctx, *, song_name):
        search_results = await search_youtube(song_name, 10)
        if not search_results:
            await ctx.send(f"Sorry, unable to find any good matches for the song '{song_name}'.")
            return

        formatted_search = '\n'.join([f"{index + 1}): {song.title}" for index, song in enumerate(search_results)])
        message_content = f"Search Results for '{song_name}':\n{formatted_search}\n\nClick on the number you want to play.\nOr add the emoji youself if you don't want to wait for buttons 1-10 to load."
        results_message = await ctx.send(message_content)

        reactions_subset = MusicPlayer.SELECTION_REACTS[:len(search_results)]
        async def send_reactions():
            for emoji in reactions_subset:
                await results_message.add_reaction(emoji)

        try:
            # We want the user to be able to react even before all the reactions have been sent, so we send them concurrenlty while waiting for a response
            verify_response = lambda reaction, user: user == ctx.author and reaction.emoji in reactions_subset
            _, (user_reaction, _) = await asyncio.gather(send_reactions(), self.bot.wait_for('reaction_add', timeout=20.0, check=verify_response))
        except asyncio.TimeoutError:
            await ctx.send("You haven't made a valid selection for 20 seconds, so the search has been cancelled.")
            return

        song = search_results[reactions_subset.index(user_reaction.emoji)]
        music_listener = self.music_listeners[ctx.guild.id]
        await music_listener.queue_lock.acquire()
        music_listener.queue.append(song)
        music_listener.queue_lock.release()
        if music_listener.playing or not await self.start_playing(ctx):
            await ctx.send(f"Queued {song.title}")

    async def start_playing(self, ctx):
        voice_client = await self.join_voice_channel(ctx)
        if not voice_client:
            return False

        music_listener = self.music_listeners[ctx.guild.id]
        music_listener.playing = music_listener.queue.pop()

        loop = asyncio.get_event_loop()
        play_next = lambda error: asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop)
        voice_client.play(discord.FFmpegPCMAudio(music_listener.playing.audio_url), after=play_next)
        await ctx.send(f"Now Playing: {music_listener.playing.title}\nhttps://youtube.com{music_listener.playing.video_url}")
        return True

    async def play_next(self, ctx):
        music_listener = self.music_listeners[ctx.guild.id]
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if len(music_listener.queue) == 0:
            music_listener.playing = None
            await voice_client.disconnect()
        else:
            await self.start_playing(ctx)

    @commands.command(name="queue", help="displays music queue")
    async def show_queue(self, ctx):
        music_queue = self.music_listeners[ctx.guild.id].queue
        if len(music_queue) == 0:
            await ctx.send("The queue is currently empty. Try adding a song with !play <song_name>.")
        else:
            formatted_queue = '\n'.join([f"{index + 1}): {song.title}" for index, song in enumerate(music_queue)])
            await ctx.send(f"The current queue is:\n{formatted_queue}")

    @commands.command(name="song", help="displays currently playing song")
    async def display_song(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        music_listener = self.music_listeners[ctx.guild.id]
        if music_listener.playing and voice_client and voice_client.is_connected():
            await ctx.send(f"The currently playing song is: {music_listener.playing.title}\n{music_listener.playing.video_url}")
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
            await voice_client.disconnect()
            print(f"Disconnected from voice channel in: {ctx.guild}")
        else:
            await ctx.send("I don't think I'm in a voice channel.")

    @commands.command(name="join", help="makes the bot join your voice channel")
    async def join_voice_channel(self, ctx):
        if not ctx.author.voice:
            await ctx.send("I can't play a song if you're not in a voice channel!")
            return None

        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if not voice_client or not voice_client.is_connected():
            return await ctx.author.voice.channel.connect()
        elif voice_client.channel != ctx.author.voice.channel:
            await voice_client.move_to(ctx.author.voice.channel)
        return voice_client

    @commands.command(name="volume", help="adjust the volume of the bot")
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
            song = music_queue.pop(song_pos - 1)


def setup(bot):
    bot.add_cog(MusicPlayer(bot))
