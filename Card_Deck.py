class Card:
        def __init__(self, value, suit):
            self.value = value
            self.suit = suit

        def print_card(self):
            await ctx.send(f"{self.value} of {self.suit}")
        
class Deck:
    def __init__(self):
        self.card_deck = []
        for suit in (['Clubs','Hearts','Diamonds','Spades']):
            for value in ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J','Q','K']:
                self.card_deck.append(Card(value, suit))
        self.card_deck.append(Card('Red', 'Jokers'))
        self.card_deck.append(Card('Black', 'Jokers'))

    def draw_card(self):
        card = self.card_deck.pop()
        await ctx.send(f"{card.value} of {card.suit}")
        return card