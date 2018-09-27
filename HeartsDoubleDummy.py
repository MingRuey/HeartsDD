# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 01:56:49 2018

@author: MRChou
"""

import time
from itertools import product
from random import shuffle
from collections import namedtuple

class Card(namedtuple('Card', ['suit', 'rank'])):
    __slots__ = ()
    suit_set = {'S', 'H', 'D', 'C'}
    rank_dict = {"T": 10, "J": 11, "Q": 12, "K": 13, "A": 14, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9}
    rank_string = '**23456789TJQKA'

    def __new__(cls, suit, rank):
        assert suit in cls.suit_set, "suit must be one of 'S', 'H', 'D', 'C'"
        assert rank in cls.rank_dict.values(), "rank must be 2, 3, ..., 14 "
        return super().__new__(cls, suit, rank)

    @classmethod
    def make_card(cls, card_string):
        suit = card_string[0]
        rank = cls.rank_dict.get(card_string[1], None)
        return Card(suit=suit, rank=rank)

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.suit == other.suit and self.rank == other.rank
        else:
            return self == Card.make_card(other)

    def __hash__(self):
        return hash(self.suit) ^ hash(self.rank)

    def __repr__(self):
        return f'{self.suit}{self.rank_string[self.rank]}'


class CardNotFound(Exception):
    pass


class Player():

    def __init__(self, name):
        self.name = name
        self.hand = set()

    def play(self, card):
        try:
            self.hand.remove(card)
        except KeyError as e:
            msg = 'Player {} has no {} to play'.format(self.name, card)
            raise CardNotFound(msg) from e
        return card

    def get_remain_suits(self, heartbreak):
        if heartbreak:  # already heart break, can play anything
            return {card.suit for card in self.hand}
        else:
            suits = {card.suit for card in self.hand if card.suit != 'H'}
            if suits:
                return suits
            else:
                return {'H'}  # it has nothing but heart

    def get_playable_list(self, suit):
        cards = [card for card in self.hand if card.suit == suit]
        if not cards:  # void in suit can play any
            cards = [card for card in self.hand]
            if not cards:
                msg = 'Player {} has empty hand.'.format(self.name)
                raise CardNotFound(msg)
        return cards

    def deal_cards(self, cards):
        for card in cards:
            self.hand.add(card)

    def __str__(self):
        display = ''
        for suit in 'SHDC':
            display += str({card for card in self.hand if card.suit == suit})
            display += '  '
        return display


class _TricksLogger():

    def __init__(self):
        super().__init__()
        self.lead = 'N'
        self.leaders = []
        self.tricks = []

    def logtrick(self, trick):
        suit = trick['NESW'.find(self.lead)].suit
        rank = -1
        winner = ''
        for player, card in zip('NESW', trick):
            if card.suit == suit and card.rank > rank:
                rank = card.rank
                winner = player
        self.leaders.append(self.lead)
        self.lead = winner
        self.tricks.append(trick)

    def first_trick(self):
        return len(self.tricks) == 0


class HeartGame():

    def __init__(self, deal_cards=True):
        self.players = {'N': Player('N'),
                        'E': Player('E'),
                        'S': Player('S'),
                        'W': Player('W')
                        }

        # for recording status and resovling tricks:
        self.log = _TricksLogger()
        self.score_cards = {Card('H', rank) for rank in range(2, 15)} \
                            | {Card.make_card('CT')} \
                            | {Card.make_card('SQ')}
        if deal_cards:
            self.ShuffleDeal()

    def heartbreak(self):
        return len(self.score_cards) == 15

    def ShuffleDeal(self):
        ranks = '23456789TJQKA'
        suits = 'CDHS'
        deck = [Card.make_card(suit+rank) for suit in suits for rank in ranks]

        # note: C2 is always the 1st card in deck, and is going to 'N' player.
        first_card = deck.pop(0)
        shuffle(deck)
        deck.insert(0, first_card)

        for index, player in enumerate('NESW'):
            self.players[player].deal_cards(deck[13*index: 13*(index+1)])

    def GetPlayableTricks(self):
        if not self.log.first_trick():
            suits = self.players[self.log.lead].get_remain_suits(self.heartbreak())
            output = []
            for suit in suits:
                output += list(product(
                        *[self.players[player].get_playable_list(suit)
                        for player in 'NESW']))
        else:
            # only happen at very first trick, force N play C2
            output = []
            output += list(product([Card.make_card('C2')],
                    *[self.players[player].get_playable_list('C')
                    for player in 'ESW']))
        return output

    def _play_card(self, player, card):
        self.players[player].play(card)
        self.score_cards -= {card}

    def PlayTrick(self, trick):
        for player, card in zip('NESW', trick):
            self._play_card(player, card)
        self.log.logtrick(trick)

    def RevokeOneTrick(self):
        for player, card in zip('NESW', self.log.tricks.pop()):
            self.players[player].hand.add(card)
            if card.suit == 'H' or card == 'CT' or card == 'SQ':
                self.score_cards.add(card)
        self.log.lead = self.log.leaders.pop()

    def PrintStatus(self):
        print('Tricks: ', self.log.tricks)
        for player in 'NESW':
            print(player, ': ', self.players[player])


def recursive_play():

    game = HeartGame()
    rnd = 0  # actually rnd should always equal to len(game.log.tricks)
    search_list = {rnd: None for rnd in range(13)}

    while rnd >= 0:
        if game.score_cards:
            if search_list[rnd] is None:
                search_list[rnd] = game.GetPlayableTricks()
            if search_list[rnd]:
                trick = search_list[rnd].pop()
                game.PlayTrick(trick)
                rnd += 1
                continue

        game.RevokeOneTrick()
        search_list[rnd] = None
        rnd -= 1


if __name__ == '__main__':
    start = time.time()
    recursive_play()
    print('Games finished, total time: ', time.time()-start)
