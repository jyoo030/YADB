import asyncio
from random import randrange

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.utils import get


class MadLibs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    MAXIMUM_STORY_ID = 188
    @commands.command(name='madlibs', help='Asks for a series of words and forms a story with those words in it')
    async def mad_libs(self, ctx, story_id: int = None):
        story_id = story_id or randrange(MadLibs.MAXIMUM_STORY_ID) + 1
        if not (1 <= story_id <= MadLibs.MAXIMUM_STORY_ID):
            await ctx.send(f"Sorry the story id '{story_id}' must be between 1 and {MadLibs.MAXIMUM_STORY_ID}")
            return

        async with aiohttp.ClientSession() as client:
            async with client.get(f"https://www.madtakes.com/libs/{story_id:03}.html") as response:
                soup = BeautifulSoup(await response.content.read(), 'html.parser')

        await ctx.send(soup.title.text)
        check_response = lambda message: message.author == ctx.author and message.channel == ctx.channel

        user_words = {}
        madlids_form = soup.find(class_="mG_form")

        # each row has a word we would ask for, we ignore the last row of the form which is a just button
        # TODO: Add sanitization based on word type (i.e. NUMBER types should be made sure as a number)
        for word_row in madlids_form.find_all("tr")[:-1]:
            word_type = word_row.find('td').text
            word_id = word_row.find('input').get('id')

            try:
                await ctx.send(f"Please enter a {word_type}:")
                user_response = await self.bot.wait_for('message', check=check_response, timeout=30)
                user_words[word_id] = user_response.content.lower()
            except asyncio.TimeoutError:
                await ctx.send("Sorry, you didn't respond in time. Please respond within 30 seconds!")
                break

        # madtakes site has hidden word ids for reused words found in hidden inputs
        # we ignore the last two hidden inputs because they are for randomization and word count
        for hidden_input in madlids_form.find_all("input", type="hidden")[:-2]:
            word_id = hidden_input.get("id")
            source_id = f"w{hidden_input.get('value')[2:-1]}"
            if source_id in user_words:
                user_words[word_id] = user_words[source_id]

        story_text = soup.find(class_="mG_glibbox")
        for newline in story_text.select('br'):
            newline.replace_with('\n')
        for word_element in story_text.select("span", class_="mG_glibword"):
            # every id in the word element is prefixed with 'mG_' so we substring it out
            word_id = word_element.get("id")[3:]
            word_element.replace_with(f"**__ {user_words.get(word_id, '[word not submitted]')} __**")
        await ctx.send(str(story_text.text).strip())


def setup(bot):
    bot.add_cog(MadLibs(bot))
