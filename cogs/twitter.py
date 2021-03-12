import os, sys
import asyncio

import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from dotenv import load_dotenv

import tweepy

class Twitter(commands.cog):
    def __init__(self, bot):
        self.bot = bot