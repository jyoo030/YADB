import os, sys
import asyncio

import discord
from discord.ext import commands
from discord.utils import get

from requests_html import HTMLSession
from bs4 import BeautifulSoup
import random as rand

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

class MadLibs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='madlibs', help='Asks for a series of words and forms a story with those words in it')
    async def mad_libs(self, ctx):
        num = '{:03}'.format(rand.randrange(1, 189))
        url = f"https://www.madtakes.com/libs/{num}.html"
        session = HTMLSession()
        res = session.get(url)
        soup = BeautifulSoup(res.content, 'html.parser')

        title = res.html.find('title', first=True).text

        user_inputs = soup.find(style='margin-bottom: 20px')

        text_chunk = soup.find(bgcolor='#d0d0d0')
        for i in text_chunk.select('br'):
            i.replace_with('\n')
        string = str(text_chunk.text).strip()

        def countWord(word):

            numWord = 0
            for i in range(1, len(word)-1):
                if word[i-1:i+3] == 'WORD':
                    numWord += 1
            return numWord

        input_list = []
        inputs = user_inputs.find_all('td', align='right')
        for word in inputs:
            input_list.append(word.text)

        id_list = []
        num_words = countWord(string)
        for i in range(1, num_words+1):
            ids = str(user_inputs.find(id=f"w{i}"))
            if 'hidden' in ids:
                index = ids.find('value')
                id_num = ids[index+9]
            else:
                index = ids.find('id')
                id_num = ids[index+5]
            id_list.append(id_num)

        word_dict = {}
        counter = 0

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for i in range(num_words):
            num = id_list[i]
            if int(num) in word_dict.keys():
                word_dict[i+1] = word_dict[int(num)]
            elif counter<len(input_list):
                try:
                    await ctx.send(f"Please enter a {input_list[counter]}: ")
                    answer = await self.bot.wait_for('message', check=check, timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("Sorry, you didn't respond in time. Please respond within 30 seconds!")
                    break
        
                word_dict[i+1] = answer.content.lower()
                counter += 1

        for i in range(num_words):
            string = string.replace("WORD", word_dict[i+1], 1)
        
        await ctx.send(string)

def setup(bot):
    bot.add_cog(MadLibs(bot))