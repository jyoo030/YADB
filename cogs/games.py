import re
from random import random

import numpy as np
from discord.ext import commands


class Games(commands.Cog):
    def __init__(self):
        self.stories = {}

    @commands.command(name="coinflip", help="Randomly flips a coin for you")
    async def coin_flip(self, ctx):
        await ctx.send("Heads" if random() >= 0.5 else "Tails")

    @commands.command(name='percentagecalculator', help= 'calculates what x percent of y is')
    async def percentage_calculator(self, ctx, percentage: int, base_value: int):
        result = base_value * percentage / 100
        await ctx.send (f'{percentage}% of {base_value} is: {result}')

    MAX_DICE_COUNT = 10
    MAX_DICE_SIDES = 120
    @commands.command(name='dicetoss', help='Randomly tosses dice_count number of sides sided dice')
    async def dice_toss(self, ctx, dice_count: int, dice_sides: int):
        username = ctx.author.nick or ctx.author.name
        if not (0 < dice_count <= Games.MAX_DICE_COUNT):
            await ctx.send(f"Sorry {username}, you must roll at least one die and you cannot roll more than {Games.MAX_DICE_COUNT} dice at once!")
            return

        if not (2 <= dice_sides <= Games.MAX_DICE_SIDES):
            await ctx.send(f"Sorry {username} we have yet to overcome physics. The must be at least two sides to a dice and at most a die can have is {Games.MAX_DICE_COUNT} sides!")
            return

        rolls = np.random.randint(1, dice_sides+1, (dice_count,))
        total_message = f" for a total of {rolls.sum()}" if dice_count > 1 else ""
        await ctx.send(f"{username}, your {dice_count}d{dice_sides} roll resulted in {' + '.join(map(str, rolls))}{total_message}.")

    OWS_COMMANDS = {'start', 'add', 'delete', 'finish'}
    @commands.command(name='ows', help='Players input one words at a time to form a story.\nUse the commands from {Games.OWS_COMMANDS} to control the story.')
    async def ows(self, ctx, command: str, word: str = None):
        story = self.stories.get(ctx.guild.id, None)

        if command not in Games.OWS_COMMANDS:
            await ctx.send("Please use a valid one word story command. Valid one word story commands are: {Games.OWS_COMMANDS}")
        elif command == "start" and story is None:
            self.stories[ctx.guild.id] = []
            await ctx.send("Successfully started your one word story game!")
        elif command == "start":
            await ctx.send("You have already started a story. Please finish the previous story before beginning a new one.")
        elif story is None:
            await ctx.send("You must start a story first before using the {command} command!")
        elif command == "add" and word is None:
            raise commands.MissingRequiredArgument(ctx.command.params["word"])
        elif command == "add" and not re.search(r"\w", word):
            await ctx.send("Your addition to the story '{word}' is not a word, please make sure it is a proper word!")
        elif command == "add":
            story.append(word)
            await ctx.send("Successfully added '{word}' to the story!")
        elif command == "delete" and len(story) == 0:
            await ctx.send("Deletion failed because your story has nothing left to delete :(.")
        elif command == "delete":
            await ctx.send(f"Successfully removed '{story.pop()}' from the story!")
        elif command == "finish" and len(story) == 0:
            await ctx.send(f"There isn't a story to publish... because you haven't put anything... dumbass.")
        elif command == "finish":
            await ctx.send(f"Here is your completed story:\n\n{' '.join(story)}")
            del self.stories[ctx.guild.id]

def setup(bot):
    bot.add_cog(Games())
