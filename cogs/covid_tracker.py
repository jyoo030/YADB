import asyncio
import io
import re

import aiohttp
import discord
import pandas as pd
from discord.ext import commands


class CovidTracker(commands.Cog):
    def __init__(self):
        self.last_modified = ""
        self.covid_data = pd.DataFrame(columns=['Name'])

    # the keyword argument (which is forced after *) will be passed all command arguments as a single string
    # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#keyword-only-arguments
    @commands.command(name="covid", help="Find covid19 data by country name or the beginning of a country name. It will print the first match it finds.")
    async def covid_tracker(self, ctx, *, country_name=None):
        if not country_name:
            await ctx.send("Please pass in a full country name or at least the start of one. Usage example: !covid australia.")
            return

        df = await self.get_updated_covid_data()
        country_matches = df.loc[self.covid_data.Name.str.match(country_name, False)]

        match_count = country_matches.shape[0]
        if match_count == 0:
            await ctx.send(f"Could not find any matches for countries starting with '{country_name}'. Get a list of known countries through command '!covlist'.")
        else:
            # Only show first match because displaying too many matches may exceed character limit
            first_match = country_matches.iloc[0].to_string()
            formatted_data = re.sub(" {2,}", ": ", first_match)
            await ctx.send(f"There were {match_count} matches for prefix '{country_name}'. The first result is:```ARM\n{formatted_data}\n```")

    # This is an arbitrary number to make sure we don't print too many countries at once
    MAX_COUNTRIES_TO_PRINT = 10
    @commands.command(name="covlist", help="Get a list of searchable nations for covid19 data")
    async def covlist(self, ctx):
        df = await self.get_updated_covid_data()
        countries = sorted(df.Name.to_list(), key=str.lower)
        country_list = '\n'.join(countries)

        if len(countries) <= CovidTracker.MAX_COUNTRIES_TO_PRINT:
            await ctx.send(f"Here is the list of countries with known data:\n{country_list}")
            return

        # printing all the country names would exceed the characters allowed in a discord message so we send it as a file
        text_file = io.StringIO(country_list)
        await ctx.send("Printing all the country names as a message would be hard to read, so here's a file instead.", file=discord.File(text_file, 'covid_countries.txt'))

    COVID_DATA_URL = "https://covid19.who.int/WHO-COVID-19-global-table-data.csv"
    async def get_updated_covid_data(self):
        async with aiohttp.ClientSession() as client:
            # The If-Modified-Since header will return a 302 response if the file hasn't been modified since the last checked date
            async with client.get(CovidTracker.COVID_DATA_URL, headers={"If-Modified-Since": self.last_modified}) as response:
                if response.status == 200:
                    self.covid_data = pd.read_csv(io.BytesIO(await response.content.read()))
                    self.last_modified = response.headers.get("Last-Modified")
        return self.covid_data


def setup(bot):
    bot.add_cog(CovidTracker())
