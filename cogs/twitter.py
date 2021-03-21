import os, sys
import asyncio

import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from dotenv import load_dotenv
from datetime import datetime
from pytz import timezone

import tweepy

load_dotenv()

# Authenticate to Twitter
auth = tweepy.OAuthHandler(os.getenv("TWITTER_CONSUMER"), os.getenv("TWITTER_CONSUMER_SECRET"))
auth.set_access_token(os.getenv("TWITTER_ACCESS"), os.getenv("TWITTER_ACCESS_SECRET"))
api = tweepy.API(auth)
if (api.verify_credentials() == False):
    print("Credential failure :'(")

class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._loop = asyncio.get_event_loop()
        self.seen_follow_list = set()
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.listener = MyStreamListener(tweet_to_discord=self.tweet_to_discord, loop=self._loop)
        self.myStream = tweepy.Stream(auth=api.auth, listener=self.listener)

    @commands.command(name="follow", help="follow @handle will give live updates of tweets")
    async def follow(self, ctx, *, handle):
        if "twitter" not in [channel.name for channel in ctx.guild.text_channels]:
            category = discord.utils.get(ctx.guild.categories, name="Text Channels")
            await ctx.guild.create_text_channel("twitter", category=category, position=len(category.channels))

        try:
            user = api.get_user(screen_name=handle)
        except tweepy.TweepError as tweep:
            if tweep.api_code == 50:
                await ctx.send("User not found. Please make sure they're public and spelled properly")
            else:
                await ctx.send("Unknown error. Please contact dev to report error.")
            return

        if user.id_str not in self.bot.guild_list[ctx.guild.id]['twitter']:
            self.bot.guild_list[ctx.guild.id]['twitter'].add(user.id_str) 
        else:
            await ctx.send("User already being followed")
            return

        if self.myStream.running is True:
            self.myStream.disconnect()
            del self.myStream
            self.myStream = tweepy.Stream(auth=api.auth, listener=self.listener)
        #FIXME: Can this be done in a list comprehension?
        full_follow_set = set()
        for guild in self.bot.guild_list:
            full_follow_set = full_follow_set | self.bot.guild_list[guild]['twitter']
        self.myStream.filter(follow=list(full_follow_set), is_async=True)

        await ctx.send(f"user @{user.screen_name} is now being followed :bird:")
    
    async def tweet_to_discord(self, message):
        if not message.in_reply_to_status_id and not message.in_reply_to_user_id and not message.in_reply_to_screen_name:
            message_url = f"http://twitter.com/{message.user.screen_name}/status/{message.id}"
            #FIXME: message.created_at is a datetime object but current can't get it to format to timezone
            # formatted_time = timezone('US/Pacific').localize(message.created_at)
            # formatted_time = formatted_time.strftime("%B %d %Y %I:%M %p")
            formatted_time = datetime.now(timezone('US/Pacific')).strftime("%B %d %Y %I:%M %p")

            # get a list of guild id's that have the message author in their follow list
            notify_id_list = [guild_id for guild_id in self.bot.guild_list if message.user.id_str in self.bot.guild_list[guild_id]['twitter']]
            # get a list of lists of channel objects for guilds that have an id in notify_id_list
            notify_guild_list = [guild.channels for guild in self.bot.guilds if guild.id in notify_id_list]
            # get a list of twitter channels from valid guilds
            channel_list = [channel for channel_list in notify_guild_list for channel in channel_list if channel.name == "twitter"]

            for channel in channel_list:
                await channel.send(f"On {formatted_time}:\n {message_url}")


class MyStreamListener(tweepy.StreamListener):
    def __init__(self, tweet_to_discord, loop):
        super(MyStreamListener, self).__init__()
        self.tweet_to_discord = tweet_to_discord
        self.loop = loop
        print("Twitter listener online")

    def on_status(self, status):
        asyncio.run_coroutine_threadsafe(self.tweet_to_discord(status), self.loop)

    def on_error(self, status_code):
        print(status_code)
        if status_code == 420:
            print("Hit Error 420")
            return False


#TODO: Add followers class to allow serverside backup of guild dictionary
# class Followers():
#     def __init__(self):
#         self.followers = []
#         self.filename = "followers.txt"
#         self.backup = self.intialize_follower_list()

#     def intialize_follower_list(self):
#         try:
#             return open(self.filename, "x")
#         except:
#             return open(self.filename, "a")

#     def add_follower(self, handle):
#         user = api.lookup_users(handle)
#         self.followers.append(user.id)

#     def print_followers(self):
#         for follower in self.followers:
#             print(follower + "\n")

#     def backup_follower_list(self):
#         for follower in self.followers:
#             self.backup.write(follower + "\n")

def setup(bot):
    bot.add_cog(Twitter(bot))

