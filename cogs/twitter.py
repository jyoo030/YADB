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
auth.set_access_token(os.getenv("TWITTER_ACCESS"), os.getenv("TWITTER_ACCESS_SECRET"))
api = tweepy.API(auth)
if (api.verify_credentials() == False):
    print("Credential failure :'(")

class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._loop = asyncio.get_event_loop()
        self.followers = Followers()
        self.follow_list = []
        self.seen_follow_list = set()
        
    @commands.Cog.listener()
    async def on_ready(self):
        stream_listener = MyStreamListener(send_msg=self.tweet_to_discord, loop=self._loop)
        self.myStream = tweepy.Stream(auth=api.auth, listener=stream_listener)

    @commands.command(name="follow", help="follow @handle will give live updates of tweets")
    async def follow(self, ctx, *, handle):
        try:
            user = api.get_user(screen_name=handle)
        except tweepy.TweepError as tweep:
            if tweep.api_code == 50:
                await ctx.send("User not found. Please make sure they're public and spelled properly")
            else:
                await ctx.send("Unknown error. Please contact dev to report error.")
            return

        if user.id_str not in self.seen_follow_list:
            self.seen_follow_list.add(user.id_str)
            self.follow_list.append(user.id_str)
        else:
            await ctx.send("User already being followed")
            return

        if self.myStream.running is True:
            self.myStream.disconnect()
        self.myStream.filter(follow=self.follow_list, is_async=True)

        await ctx.send(f"user @{user.screen_name} is now being followed :bird:")
    
    async def tweet_to_discord(self, message):
        if not message.in_reply_to_status_id and not message.in_reply_to_user_id and not message.in_reply_to_screen_name:
            message_url = f"http://twitter.com/{message.user.screen_name}/status/{message.id}"
            general = discord.utils.get(self.bot.guilds[0].channels, name="justins-bot-lab")
            await general.send(message_url)


class MyStreamListener(tweepy.StreamListener):
    def __init__(self, send_msg, loop):
        super(MyStreamListener, self).__init__()
        self.send_msg_discord = send_msg
        self.loop = loop
        print("Listener booted up")

    def on_status(self, status):
        future = asyncio.run_coroutine_threadsafe(self.send_msg_discord(status), self.loop)
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

