import os, sys
import asyncio

import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from dotenv import load_dotenv

import tweepy

load_dotenv()

# Authenticate to Twitter
auth = tweepy.OAuthHandler(os.getenv("TWITTER_CONSUMER"), os.getenv("TWITTER_CONSUMER_SECRET"))
auth.set_access_token("TWITTER_ACCESS", "TWITTER_ACCESS_SECRET")
api = tweepy.API(auth)
if (api.verify_credentials() == False):
    print("Credential failure :'(")

class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._loop = asyncio.get_event_loop()
        self.followers = Followers()
        
    @commands.command(name="get_recent", help="Get's the most recent tweet from someones twitter")
    async def get_recent(self, ctx):
        tweets = api.user_timeline(screen_name="TestYadb", count=1)
        await ctx.send(f":bird: User {tweets[0].user.screen_name}'s most recent tweet is:\n {tweets[0].text}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        stream_listener = MyStreamListener(send_msg=self.tweet_to_discord, loop=self._loop)
        self.myStream = tweepy.Stream(auth=api.auth, listener=stream_listener)
        self.myStream.filter(follow=["1370481755640135680"], is_async=True)
    
    async def tweet_to_discord(self, message):
        # guild = await self.bot.get_guild("766003288456953896")
        # print(guild)
        screen_name = message.user.screen_name
        message_url = f"http://twitter.com/{screen_name}/status/{message.id}"
        general = discord.utils.get(self.bot.guilds[0].channels, name="justins-bot-lab")
        await general.send(message_url)


class MyStreamListener(tweepy.StreamListener):
    def __init__(self, send_msg, loop):
        super(MyStreamListener, self).__init__()
        self.send_msg_discord = send_msg
        self.loop = loop
        print("Listener booted up")

    def on_status(self, status):
        self.send_message(status)
    
    def send_message(self, msg):
        future = asyncio.run_coroutine_threadsafe(self.send_msg_discord(msg), self.loop)
        future.result()

    def on_error(self, status_code):
        print(status_code)
        if status_code == 420:
            print("Hit Error 420")
            return False

class Followers():
    def __init__(self):
        self.followers = []
        self.filename = "followers.txt"
        self.backup = self.intialize_follower_list()

    def intialize_follower_list(self):
        try:
            return open(self.filename, "x")
        except:
            return open(self.filename, "a")

    def add_follower(self, handle):
        user = api.lookup_users(handle)
        self.followers.append(user.id)

    def print_followers(self):
        for follower in self.followers:
            print(follower + "\n")

    def backup_follower_list(self):
        for follower in self.followers:
            self.backup.write(follower + "\n")

def setup(bot):
    bot.add_cog(Twitter(bot))

