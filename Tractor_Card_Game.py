import random
from card_deck import Deck

import os
from os import system
import asyncio

import discord
from discord.ext import commands
from discord.utils import get

# @bot.command(name='tractor', help='Starts a tractor card game for 4 players')
class TractorGame(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    class Player():
        def __init__(self, userid):
            self.userid = userid
            self.hand = []
            self.points = 0 
            self.trump_rank = 2

        def view_hand(self):
            for card in self.hand:
                await ctx.send(f"{card.value} of {card.suit}")
            return

    playerlist = []

    for num in range(4):
        playerlist.append(Player())
        
    def count_points():
    team1_total = playerlist[0].points + playerlist[1].points
    team2_total = playerlist[2].points + playerlist[3].points

    deck1 = Deck()
    deck2 = Deck()
    all_cards = deck1.card_deck + deck2.card_deck
    random.shuffle(all_cards)

    while (len(all_cards)>8): # 25 cards per player and 8 cards left over
        for i in range (4):
            playerlist[i].hand.append(all_cards.pop())
            playerlist[i].hand[-1]

def setup(bot):
    bot.add_cog(TractorGame(bot))