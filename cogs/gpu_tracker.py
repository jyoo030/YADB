import os
import asyncio
from arsenic import get_session
from arsenic.browsers import Firefox
from arsenic.services import Geckodriver

import discord
from discord.ext import commands

class GPUTracker(commands.Cog):
    def __init__(self):
        self.BB_3080_URL = "https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory=abcat0507002&id=pcat17071&iht=n&ks=960&list=y&qp=gpusv_facet%3DGraphics%20Processing%20Unit%20(GPU)~NVIDIA%20GeForce%20RTX%203080&sc=Global&st=categoryid%24abcat0507002&type=page&usc=All%20Categories"
        # self.BB_3080_URL= "https://www.bestbuy.com/site/computer-cards-components/video-graphics-cards/abcat0507002.c?id=abcat0507002"

    @commands.command(name="track", help="Adds a tracker for GPU Drops from Best Buy")
    async def track_gpu(self, ctx):
        await ctx.send("Tracking RTX 3080 from Best Buy")
        async with get_session(Geckodriver(), Firefox(**{'moz:firefoxOptions': {'args': ['-headless']}})) as session:
            while True:
                await asyncio.gather(
                        asyncio.sleep(60),
                        self.check_gpu_status(session, ctx)
                        )

    async def check_gpu_status(self, session, ctx):
        await session.get(self.BB_3080_URL)
        items = await session.get_elements('ol')
        gpu_items_raw = await items[1].get_text()
        gpu_items_split = gpu_items_raw.splitlines()
        gpu_items_split.remove("ADVERTISEMENT")
        lines_per_group = 8
        gpu_items_grouped = [gpu_items_split[i:i+lines_per_group] for i in range(0, len(gpu_items_split), lines_per_group)]
        d_msg = ""
        for gpu in gpu_items_grouped:
            if gpu[7] == "Add to Cart":
                d_msg += "Item " + gpu[0] + " is in stock!\n" 
        if d_msg != "":
            d_msg += self.BB_3080_URL
            await ctx.send(d_msg)

def setup(bot):
    bot.add_cog(GPUTracker())
