import asyncio

import discord
from discord.ext import commands
from discord.utils import get

from utilities.CovidDownloader import csvDownloader

class CovidTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="covid", help="Find Covid19 info for a country. Please input full name with proper capitalization")
    async def covidTracker(self, ctx, *, country_name):

        try: 
            await ctx.send(csvDownloader().find_data(str(country_name)))

        except Exception as err:
            await ctx.send("You might have inputted a country name that I cannot identify. You can access the list of identified nations by typing '?covlist'")
            raise err

    @commands.command(name="covlist", help="Find list of searchable nations for Covid19 data")
    async def covlist (self, ctx):
        half_length = len(csvDownloader().country_list()) // 2
        await ctx.author.send(', '.join(csvDownloader().country_list()[:half_length]))
        await ctx.author.send(', '.join(csvDownloader().country_list()[-half_length:]))
        await ctx.author.send('You would need to copy and paste the full names of each nation when using command "covid"')

def setup(bot):
    bot.add_cog(CovidTracker(bot))