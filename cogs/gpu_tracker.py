import os
import asyncio
from random import randrange

import discord
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
import aiohttp
from lxml import html

class GPUTracker(commands.Cog):
    def __init__(self):
        # self.BB_3080_URL = "https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory=abcat0507002&id=pcat17071&iht=n&ks=960&list=y&qp=gpusv_facet%3DGraphics%20Processing%20Unit%20(GPU)~NVIDIA%20GeForce%20RTX%203080&sc=Global&st=categoryid%24abcat0507002&type=page&usc=All%20Categories"
        self.item_keys = ['name', 'price', 'status']
        self.BB_3080_URL = "https://www.bestbuy.com/site/computer-cards-components/video-graphics-cards/abcat0507002.c?id=abcat0507002"
        self.BASE_URL = "https://www.bestbuy.com"


    @commands.command(name="track", help="Adds a tracker for GPU Drops from Best Buy")
    async def track_gpu(self, ctx):
        await ctx.send("Tracking RTX 3080 from Best Buy")
        self.check_gpu_status.start(ctx)

    @tasks.loop(seconds=60*randrange(1,2))
    async def check_gpu_status(self, ctx):
        print("Checking for gpus...")
        user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0"
        headers = {'User-Agent': user_agent, "cache-control": "max-age=0"}

        async with aiohttp.ClientSession() as session:
            async with session.get(self.BB_3080_URL, headers=headers) as resp:
                tree = html.fromstring(await resp.text())

                name = tree.xpath('//*[@id="main-results"]/ol/li/div/div/div/div/div/div[2]/div[1]/div[2]/div/h4/a/text()')
                href = tree.xpath('//*[@id="main-results"]/ol/li/div/div/div/div/div/div[2]/div[1]/div[2]/div/h4/a/@href')
                price = tree.xpath('//*[@id="main-results"]/ol/li/div/div/div/div/div/div[2]/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/div/div/span[1]/text()')
                status = tree.xpath('//*[@id="main-results"]/ol/li/div/div/div/div/div/div[2]/div[2]/div[3]/div/div/div/div/div/div/button/text()')
                for i in range(len(status)):
                    if status[i] == "Add to Cart":
                        await ctx.send(f"{name[i]} in stock:\nprice: {price[i]}\nlink: {self.BASE_URL}{href[i]}\n")

    @commands.command(name="stoptrack", help="stops gpu tracker")
    async def stop_track_gpu(self, ctx):
        self.check_gpu_status.stop()
        await ctx.send("3080 tracker stopped")

    @commands.command(name="trackURL", help="changes the tracked URL")
    async def trackURL(self, ctx, url):
        self.BB_3080_URL = url
        self.check_gpu_status.cancel()
        await self.track_gpu(ctx)

def setup(bot):
    bot.add_cog(GPUTracker())
