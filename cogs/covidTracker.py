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
        csvDownloader().find_data(country_name)
        await ctx.send(csvDownloader().find_data)

def setup(bot):
    bot.add_cog(CovidTracker(bot))