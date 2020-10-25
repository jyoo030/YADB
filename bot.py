import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

#region tutorial
'''
DECORATOR 
the @bot.event is a decorator provided by discord.py what this means 
is that it does something before, after or before and after a function is run. 
So when you apply @something, imagine it actually looks like this:

Run some code here
on_ready()
Run some code here
-----------------------------------------------------------------------------
ASYNC
async functions are allowed to run at the same time as other functions. 
This is useful, because imagine if multiple people gave the bot commands, and the
bot had to wait before each one finished before starting the next one. 
The program would lag and feel terrible. Async allows multiple functions
to run at the same time, so one user could, say request music from the bot
while another is playing a game of blackjack with the bot.
-----------------------------------------------------------------------------
AWAIT
await is a keyword unique to async functions. It can only be run within async functions.
You use await when calling async functions within async functions. This tells python
to stop running code at that line, and go do other things while that code returns. 
So, await member.create_dm() will tell python to start creating a dm, but don't try
to send a message until the dm channel is created, because you can't send a message
without a dm channel. In the meantime, python will go handle other stuff that may be running. 
'''

# Jonathan shouldn't have put his phone underwater.  

# Use on_ready() for debug purposes.
# @bot.event
# async def on_ready():
#     guild = discord.utils.get(bot.guilds, name=GUILD)
#     members = '\n - '.join([member.name for member in guild.members])

#     print(
#         f'{bot.user} is connected to the following guild:\n'
#         f'{guild.name} (id: {guild.id})\n'
#         f'Guild Members: \n - {members}'
#     )
#endregion

@bot.event
async def on_ready():
    print(f'Logged in as:\n\tUser: {bot.user.name}\n\tID: {bot.user.id}\n\tVersion: {discord.__version__}\n')

@bot.event
async def on_member_join(member):
    await member.send("Imagine.")

@bot.event
async def on_guild_join(guild):
    for category in guild.categories:
        if category.name == 'Text Channels':
            text_category = category
        elif category.name == 'Voice Channels':
            voice_category = category
        else:
            print('Welp. Ur dumb.')

    await guild.create_text_channel('among-us', category=text_category)
    await guild.create_text_channel('memes', category=text_category)
    await guild.create_voice_channel('Among Us', category=voice_category)
    await guild.create_voice_channel('League', category=voice_category)
    await guild.create_voice_channel('AFK', category=voice_category)

@bot.command(name='text', help='prints some random text')
async def bot_text(ctx):
    await ctx.send("Hello this is some random text!")

@bot.command(name='coinflip', help='Randomly flips a coin for you')
async def coin_flip(ctx):
    flip= random.randint (0,2)

    if (flip==0):
        await ctx.send("Heads")
    else:
        await ctx.send("Tails")

@bot.command(name='madlibs', help='Asks for a series of words and forms a story with those words in it')
async def mad_libs(ctx):
    
if __name__ == '__main__':
    bot.load_extension('music')
bot.run(TOKEN)