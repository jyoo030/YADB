import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv
import pytz

import tweepy


class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        # Authenticate to Twitter
        auth = tweepy.OAuthHandler(os.getenv("TWITTER_CONSUMER"), os.getenv("TWITTER_CONSUMER_SECRET"))
        auth.set_access_token(os.getenv("TWITTER_ACCESS"), os.getenv("TWITTER_ACCESS_SECRET"))
        self.api = tweepy.API(auth)
        if not self.api.verify_credentials():
            print("Failed to Authenticate Credentials for Twitter API :(")

    @commands.Cog.listener()
    async def on_ready(self):
        self.twitter_follows = self.bot.guild_list["twitter"]
        self.listener = TwitterListener(tweet_to_discord=self.tweet_to_discord, loop=asyncio.get_event_loop())
        self.tweet_stream = None

    @commands.command(name="follow", help="follow @handle will give live updates of tweets")
    async def follow(self, ctx, *, handle):
        if "twitter" not in [channel.name for channel in ctx.guild.text_channels]:
            category = discord.utils.get(ctx.guild.categories, name="Text Channels")
            await ctx.guild.create_text_channel("twitter", category=category, position=len(category.channels))

        user = await self.get_user(handle, ctx)
        if user:
            if user.id_str not in self.twitter_follows:
                self.twitter_follows[user.id_str]
                self.refresh_stream()

            if ctx.guild.id in self.twitter_follows[user.id_str]:
                await ctx.send(f"User @{user.screen_name} already being followed")
                return

            self.twitter_follows[user.id_str].add(ctx.guild.id)
            await ctx.send(f"user @{user.screen_name} is now being followed :bird:")

    @commands.command(name="unfollow", help="unfollows @handle")
    async def unfollow(self, ctx, *, handle):
        user = await self.get_user(handle, ctx)
        if user:
            if user.id_str not in self.twitter_follows or ctx.guild.id not in self.twitter_follows[user.id_str]:
                await ctx.send(f"User @{handle} isn't being followed.")
            else:
                self.twitter_follows[user.id_str].remove(ctx.guild.id)
                if not self.twitter_follows[user.id_str]:
                    del self.twitter_follows[user.id_str]
                    self.refresh_stream()

                await ctx.send(f"User @{handle} is no longer being followed.")

    def refresh_stream(self):
        if self.tweet_stream:
            self.tweet_stream.disconnect()

        # tweepy is dumb and doesn't actually disconnect on demand until a new tweet sends
        if self.twitter_follows:
            self.tweet_stream = tweepy.Stream(auth=self.api.auth, listener=self.listener)
            self.tweet_stream.filter(follow=list(self.twitter_follows.keys()), is_async=True)

    async def get_user(self, handle, ctx):
        try:
            return self.api.get_user(screen_name=handle)
        except tweepy.TweepError as tweep:
            if tweep.api_code == 50:
                await ctx.send("User not found. Please make sure they're public and spelled properly")
            else:
                await ctx.send(f"Unknown error. Please contact dev with error code: {tweep.api_code}.")
            return None

    async def tweet_to_discord(self, message):
        if not message.in_reply_to_status_id and not message.in_reply_to_user_id and not message.in_reply_to_screen_name:
            message_url = f"http://twitter.com/{message.user.screen_name}/status/{message.id}"

            creation_date_pst = message.created_at.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Pacific"))
            formatted_time = creation_date_pst.strftime("%B %d %Y %I:%M %p")

            # get all servers currently following this twitter user
            follower_guilds = [guild for guild in self.bot.guilds if guild.id in self.bot.guild_list["twitter"][message.user.id_str]]
            # get the servers' twitter channel
            follower_channels = [channel for guild in follower_guilds for channel in guild.channels if channel.name == "twitter"]

            discord_message = f"On {formatted_time}:\n {message_url}"
            await asyncio.gather(*[channel.send(discord_message) for channel in follower_channels])


class TwitterListener(tweepy.StreamListener):
    def __init__(self, tweet_to_discord, loop):
        super(TwitterListener, self).__init__()
        self.tweet_to_discord = tweet_to_discord
        self.loop = loop
        print("Twitter listener online")

    def on_status(self, status):
        asyncio.run_coroutine_threadsafe(self.tweet_to_discord(status), self.loop)

    def on_error(self, status_code):
        print(f"Error Code: {status_code}")
        if status_code == 420:
            # returning False turns off the stream
            # 420 error means we're making too many calls to API
            return False
        return True


def setup(bot):
    try:
        bot.add_cog(Twitter(bot))
    except tweepy.TweepError as error:
        print("Failed to load twitter cog due to error in authentication (probably missing credentials) or api connection. It produced the following error message:")
        print(f">   '{error}'")
        print()
