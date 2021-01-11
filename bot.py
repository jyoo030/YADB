import os, sys

import discord
from discord.ext import commands
from dotenv import load_dotenv
import random


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.guild_list = {}

@bot.event
async def on_ready():
    print(
        f"Logged in as:\n\tUser: {bot.user.name}\n\tID: {bot.user.id}\n\tVersion: {discord.__version__}\n"
    )
    for guild in bot.guilds:
        add_to_guilds(guild.id)
    
def add_to_guilds(guild_id):
    bot.guild_list.setdefault(guild_id, {})
    bot.guild_list[guild_id].setdefault("queue", [])
    bot.guild_list[guild_id].setdefault("curr_song", "")

@bot.event
async def on_member_join(member):
    await member.send("Imagine.")

@bot.event
async def on_guild_join(guild):
    add_to_guilds(guild.id)

@bot.event
async def on_member_remove(member):
    general = discord.utils.get(member.guild.channels, name="sayonara")
    if member.nick == None:
        await general.send(f"Goodbye, {member}")
    else:
        await general.send(f"Goodbye, {member}, also known as {member.nick}")

@bot.command(name="coinflip", help="Randomly flips a coin for you")
async def coin_flip(ctx):
    flip = random.randint(0, 2)

    if flip == 0:
        await ctx.send("Heads")
    else:
        await ctx.send("Tails")

@bot.command(name='percentagecalculator', help= 'calculates what x percent of y is')
async def percentageCalculator(ctx,*parameter):
    x = parameter[0]
    y = parameter[1]
    await ctx.send (f'{x}% of {y} is: {int(x)/100 * int(y)}' )

@bot.command(name='dicetoss', help='Randomly tosses x number of y sided dice with the command dicetoss xdy')
async def dice_toss(ctx, parameter):
    dice_total = 0
    toss_list = []

    parameter = parameter.split('d')
    
    if (int(parameter[0])>10):
        await ctx.send('You cannot roll more than 10 dice!')
    elif (int(parameter[1])>20):
        await ctx.send('You cannot have a dice with more than 20 sides!')
    else:
        for i in range(int(parameter[0])):
            toss = random.randint(1,int(parameter[1]))
            toss_list.append(toss)
            dice_total += toss
            formatted_output = ' + '.join(str(toss) for toss in toss_list)

        if parameter[0] == "1":
            await ctx.send(f"{ctx.author}, your roll is: \n{dice_total}")
        else:
            await ctx.send(f"{ctx.author}, your rolls are: \n{formatted_output}\nfor a total of: \n{dice_total}")
    
story = []
valid_input = ['start', 'add', 'delete', 'finish']
@bot.command(name='ows', help='Players input one words at a time to form a story. \n"ows start" starts a new story" \n"ows delete" deletes the most recent addition \n"ows finish" finishes the story and gives you the completed story.')
async def ows(ctx, *parameter):
    if parameter[0] not in valid_input:
        await ctx.send("Please use a valid input. Valid keywords are: start, add, delete, finish")
        
    elif len(story) == 0:
        if parameter[0] == "start":
            await ctx.send("One Word Story game started!")
            story.append("   ")
        else:
            await ctx.send("You must start a story first!")

    else:
        if parameter[0] == "start":
            await ctx.send("You have already started a story. Please finish the previous story before beginning a new one.")
        elif parameter[0] == "add":
            story.append(parameter[1])
        elif parameter[0] == "delete":
            await ctx.send(f'Removed the word "{story.pop()}" from the one word story')
        elif parameter[0] == "finish":
            if len(story) > 1:
                await ctx.send(" ".join(story))
                story.clear()
            else:
                await ctx.send("Haven't put anything into the story dumbass")
        else:
            print("Shouldn't ever get here but aight")

    
if __name__ == "__main__":
    bot.load_extension("cogs.music")
    bot.load_extension("cogs.madlibs")
    
bot.run(TOKEN)
