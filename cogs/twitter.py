import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
import pytz

import tweepy

load_dotenv()

# Authenticate to Twitter
auth = tweepy.OAuthHandler(os.getenv("TWITTER_CONSUMER"), os.getenv("TWITTER_CONSUMER_SECRET"))
auth.set_access_token(os.getenv("TWITTER_ACCESS"), os.getenv("TWITTER_ACCESS_SECRET"))


class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._loop = asyncio.get_event_loop()
        self.authenticate()

    def authenticate(self):
        self.api = tweepy.API(auth)
        if not self.api.verify_credentials():
            print("Failed to Authenticate Credentials for Twitter API :(")

    @commands.Cog.listener()
    async def on_ready(self):
        self.listener = TwitterListener(tweet_to_discord=self.tweet_to_discord, loop=self._loop)
        self.tweet_stream = tweepy.Stream(auth=self.api.auth, listener=self.listener)

    @commands.command(name="follow", help="follow @handle will give live updates of tweets")
    async def follow(self, ctx, *, handle):
        if "twitter" not in [channel.name for channel in ctx.guild.text_channels]:
            category = discord.utils.get(ctx.guild.categories, name="Text Channels")
            await ctx.guild.create_text_channel("twitter", category=category, position=len(category.channels))

        try:
            user = self.api.get_user(screen_name=handle)
        except tweepy.TweepError as tweep:
            if tweep.api_code == 50:
                await ctx.send("User not found. Please make sure they're public and spelled properly")
            else:
                await ctx.send(f"Unknown error. Please contact dev with error code: {tweep.api_code}.")
            return

        twitter_follows = self.bot.guild_list['twitter']
        if user.id_str in twitter_follows and ctx.guild.id in self.bot.guild_list['twitter'][user.id_str]:
            await ctx.send(f"User @{user.screen_name} already being followed")
            return

        twitter_follows.setdefault(user.id_str, [])
        twitter_follows[user.id_str].append(str(ctx.guild.id))

        if self.tweet_stream.running:
            self.tweet_stream.disconnect()
            del self.tweet_stream
            self.tweet_stream = tweepy.Stream(auth=self.api.auth, listener=self.listener)

        # all_follows = set().union(*(guild_data['twitter'] for guild_data in self.bot.guild_list.values()))
        self.tweet_stream.filter(follow=[*twitter_follows.keys()], is_async=True)
        await ctx.send(f"user @{user.screen_name} is now being followed :bird:")

    async def tweet_to_discord(self, message):
        if not message.in_reply_to_status_id and not message.in_reply_to_user_id and not message.in_reply_to_screen_name:
            message_url = f"http://twitter.com/{message.user.screen_name}/status/{message.id}"

            creation_date_pst = message.created_at.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
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
    bot.add_cog(Twitter(bot))
