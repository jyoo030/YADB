import os
import sys
import traceback
from collections import defaultdict

import discord
from discord.ext import commands
from dotenv import load_dotenv


class DefaultBotHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.guild_list = defaultdict(lambda: {"queue": [], "curr_song": ""})

    @commands.Cog.listener()
    async def on_ready(self):
        print("Logged in as:")
        print(f"    User: {self.bot.user.name}")
        print(f"    ID: {self.bot.user.id}")
        print(f"    Version: {discord.__version__}")

        for guild in self.bot.guilds:
            self.bot.guild_list[guild.id]

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.guild_list[guild.id]

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        del self.bot.guild_list[guild.id]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await member.send("Imagine.")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        general = discord.utils.get(member.guild.channels, name="sayonara")
        nickname_message = member.nick and f", also known as {member.nick}" or ""
        await general.send(f"Goodbye, {member}{nickname_message}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        parameters = list(map(str, ctx.command.params.values()))
        command_usage = f"Command usage: !{ctx.command.name} [{'] ['.join(parameters[1:])}]."
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Seems we are missing parameter '{error.param.name}'.\n{command_usage}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Seems we were passed the wrong type for a parameter: {str(error).lower()}\n{command_usage}")
        else:
            print("Shouldn't ever get here but aight")
            await ctx.send(f"Seems the command has failed.\n{command_usage}")
            # print the unexpected exception for developer reference
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.members = True
    load_dotenv()
    bot = commands.Bot(command_prefix=os.getenv("CMD"), intents=intents)
    bot.add_cog(DefaultBotHandler(bot))
    bot.load_extension("cogs.music")
    bot.load_extension("cogs.madlibs")
    bot.load_extension("cogs.games")
    bot.load_extension("cogs.covid_tracker")
    bot.load_extension("cogs.twitter")

    token = os.getenv("DISCORD_TOKEN")
    bot.run(token)
