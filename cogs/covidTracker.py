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
            await ctx.send("You might have inputted a country name that I cannot identify")
            raise err

def setup(bot):
    bot.add_cog(CovidTracker(bot))