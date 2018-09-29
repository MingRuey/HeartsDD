# -*- coding: utf-8 -*-
"""
Created on Sat Sep 29 02:22:45 2018

@author: MRChou
"""

import os
import time
import logging
import statistics
from random import shuffle
from concurrent import futures
from multiprocessing import Queue, Process
from queue import Empty

from HeartsDoubleDummy import Card,  HeartGame

DECK = {Card.make_card(suit+rank) for suit in 'SHDC' for rank in '23456789TJQKA'}
C2 = Card.make_card('C2')


def _play_one_random_game(game):
    for _ in range(13):
        trick = game.GetRandPlayableTricks()
        game.PlayTrick(trick)
    return game


def randplay_10cards_fixed(fixed_hand, num_of_games=1000):
    fixed_hand = set(fixed_hand)
    assert len(fixed_hand) == 10

    scores = []
    for count in range(num_of_games):
        game = HeartGame(deal_cards=False)

        cards_for_deal = list(DECK - fixed_hand)
        shuffle(cards_for_deal)

        esw = ['E', 'S', 'W']
        shuffle(esw)

        target_player = ''
        target_hand = fixed_hand | set(cards_for_deal[:3])
        if C2 in target_hand:
            target_player = 'N'
            game.players['N'].deal_cards(target_hand)
        else:
            target_player = esw.pop()
            game.players[target_player].deal_cards(target_hand)

        for num in range(3):
            hand = cards_for_deal[3+num*13: 3+(num+1)*13]

            if C2 in hand:
                game.players['N'].deal_cards(hand)
            else:
                game.players[esw.pop()].deal_cards(hand)

        _play_one_random_game(game)
        scores.append(game.GetScore()[target_player])

    return sum(scores)/num_of_games, statistics.stdev(scores)


class _Rand10CardsGener:

    def __init__(self, num_of_hands):
        self.num_of_hands = num_of_hands
        self.deck = list(DECK)

    def __iter__(self):
        while self.num_of_hands:
            shuffle(self.deck)
            yield self.deck[:10]
            self.num_of_hands -= 1


def _worker(hands_num, que):
    hands_gener = _Rand10CardsGener(hands_num)
    try:
        for hand in hands_gener:
            avg, stddev = randplay_10cards_fixed(hand)
            que.put((hand, avg, stddev))
    except Exception as err:
        logging.exception(err)


def _card_sort_key(card):
    return '*CDHS'.find(card.suit)*100 + card.rank


def random_games_stat(outputfile, num_of_hands):
    start_time = time.time()

    sucess_count = 0
    hands_gener = _Rand10CardsGener(num_of_hands)
    with open(outputfile, 'a') as fout:
        fout.write(''.join(['Card{:02},'.format(i) for i in range(1, 11)]))
        fout.write('Avg,Stddev\n')
        for hand in hands_gener:
            avg, stddev = randplay_10cards_fixed(hand)

            hand.sort(key=_card_sort_key, reverse=True)
            fout.write(''.join([str(card)+',' for card in hand]))
            fout.write(str(avg)+','+str(stddev)+'\n')
            sucess_count += 1

    logging.info(' ---%d of hands done' % sucess_count)
    logging.info(' ---take %s seconds' % (time.time() - start_time))
    logging.info(' ---outputfile: %s' % os.path.basename(outputfile))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s  %(message)s',
                        handlers=[logging.FileHandler('HeartsHandEvalData.log'),
                                  logging.StreamHandler()])

    outputfile = 'E:/Google_Drive/test.csv'
    random_games_stat(outputfile, 8)
