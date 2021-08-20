import pickle

import numpy as np
import random
import time
import pprint
from src.board import Board
from src.map import Map
from src.utils import *
from src.algos import flat, UCB, best_move_UCT, best_move_RAVE

MAX_DICE = 3
BLOCK = 0
RED = 1
BLUE = 2
GREEN = 3
EMPTY = 4
GOAL = -1

REF2 = "P22-D3-S34-v1"
REF3 = "P32-D3-S48-v1"

INT2STRING = {RED: 'RED', BLUE: 'BLUE'}


def generate_hash_structures(map_reference: str):
    b = Board(mapp=Map(map_reference))
    keys = list(b.board.nodes)
    nb_cases = len(keys)
    table = dict(zip(keys, np.random.randint(0, 2 ** 31, (nb_cases, b.map.nb_players+1))))

    turn = {RED: np.random.randint(0, 2**31),
            BLUE: np.random.randint(0, 2**31),
            GREEN: np.random.randint(0, 2**31)}

    return table, turn


def flat_game(board, nb_playouts, game_time_limit=100):

    figures = [board.display('names')]
    while not board.over and board.game_time < game_time_limit:
        dice_score = random.randint(1, MAX_DICE)
        best_move = flat(board, dice_score, nb_playouts)
        board.play(best_move)
        figures.append(board.display('names'))
        print('game_time :', board.game_time)

    return figures


def UCB_game(board, nb_playouts, game_time_limit=100):

    figures = [board.display('names')]
    while not board.over and board.game_time < game_time_limit:
        dice_score = random.randint(1, MAX_DICE)
        best_move = UCB(board, dice_score, nb_playouts)
        board.play(best_move)
        figures.append(board.display('names'))
        print('game_time :', board.game_time)
    return figures


def UCT_game(board, nb_playouts, game_time_limit=100, mode=1, save_gif=True):

    figures = []
    if save_gif is True:
        figures = [board.display('names')]
    while not board.over and board.game_time < game_time_limit:
        dice_score = random.randint(1, board.map.max_dice)
        start_time = time.perf_counter()
        best_move = best_move_UCT(board, dice_score, nb_playouts, mode, c=0.6)
        end_time = time.perf_counter()
        board.play(best_move)
        if save_gif is True:
            figures.append(board.display('names'))
        print('game_time :', board.game_time, f'({round(end_time-start_time,2)}s)')
    if save_gif is True:
        return figures


def play_vs_UCT(nb_playouts):
    b_test = Board(hash_table, hash_turn)
    b_test.turn = random.choice([BLUE, RED])
    print("C'est " + INT2STRING[b_test.turn] + " qui commence.")
    figures = [b_test.display('names')]

    while not b_test.over:
        dice_score = random.randint(1, MAX_DICE)

        if b_test.turn == RED:  # On jouera toujours le joueur ROUGE
            print('\n\n-----------------------------------\n\n')
            print('A vous de jouer !')
            print("Vous avez fait", dice_score)
            print("Coups possibles : ")
            valid_moves = b_test.valid_moves(dice_score)
            for i, m in enumerate(valid_moves):
                print(i, ':', m)
            figures.append(b_test.display('names'))
            plot_fig(figures[-1])
            choice = input("Quel est votre choix (format : num_coup,emplacement):\n-> ")
            l = choice.split(',')
            if len(l) == 1:
                l.append(None)
            chosen_move = valid_moves[int(l[0])]
            b_test.play(chosen_move, l[1])
            print('Vous avez joué '+chosen_move.__str__())
        else:
            print('\n\n-----------------------------------\n\n')
            print('A BLUE de jouer !')

            best_move = best_move_UCT(b_test, dice_score, nb_playouts, c=0.6)
            figures.append(b_test.display('names'))
            plot_fig(figures[-1])
            b_test.play(best_move[0], best_move[1])
            print('game_time :', b_test.game_time)
    return figures


def UCT_vs_UCT(board, nb_playouts, nb_games):
    sum_wins = {RED: 0, BLUE: 0}
    if board.map.nb_players == 3:
        sum_wins[GREEN] = 0
    for g in range(nb_games):
        b_cop = board.copy()
        print("Game "+str(g+1),end=" ")
        start_time = time.perf_counter()
        while not b_cop.over:
            dice_score = random.randint(1, board.map.max_dice)
            chosen_move_red = best_move_UCT(b_cop, dice_score, nb_playouts, mode=1)
            b_cop.play(chosen_move_red)

            if b_cop.over:
                break

            dice_score = random.randint(1, board.map.max_dice)
            chosen_move_blue = best_move_UCT(b_cop, dice_score, nb_playouts, mode=2)
            b_cop.play(chosen_move_blue)
        end_time = time.perf_counter()
        sum_wins[b_cop.winner] += 1
        print(f"- game_time : {b_cop.game_time} {round((end_time - start_time)/60,0)}min)")
        print("WINS : ")
        print("RED  -  BLUE  -  GREEN")
        pprint.pprint(sum_wins)
        with open(f"sum_wins_{nb_playouts}plyt_{g}games.pkl", "wb") as f:
            pickle.dump(sum_wins, f)




def RAVE_game(board: Board, nb_playouts, game_time_limit, mode, save_gif=False):
    figures = []
    if save_gif is True:
        figures = [board.display('names')]
    while not board.over and board.game_time < game_time_limit:

        dice_score = random.randint(1, board.map.max_dice)
        start_time = time.perf_counter()
        best_move = best_move_RAVE(board, dice_score, nb_playouts, mode)
        end_time = time.perf_counter()
        board.play(best_move)
        if save_gif is True:
            figures.append(board.display('names'))
        print('game_time :', board.game_time, f'({round(end_time - start_time, 2)}s)')
    if save_gif is True:
        return figures



if __name__ == '__main__':
    print('Debut')

    b1 = Board(*generate_hash_structures("P22-D3-S34-v1"), mapp=Map("P22-D3-S34-v1"))
    b2 = Board(*generate_hash_structures(REF3), mapp=Map("P32-D3-S48-v1"))

    UCT_vs_UCT(b1, 20, 2)

    # figs = RAVE_game(b2, 50, 150, mode=2)
    # figs2gif(figs, "UCT_3j_600plyt_mode2.gif")



