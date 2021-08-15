
import numpy as np
import random
from src.board import Board
from src.map import Map
from src.utils import *
from src.algos import flat, UCB, best_move_UCT

MAX_DICE = 3
BLOCK = 0
RED = 1
BLUE = 2
GREEN = 3
EMPTY = 4
GOAL = -1

INT2STRING = {RED: 'RED', BLUE: 'BLUE'}


def generate_hash_structures():
    b = Board()
    keys = list(b.board.nodes)
    nb_cases = len(keys)
    table = dict(zip(keys, np.random.randint(0, 2 ** 31, (nb_cases, 3))))
    turn = np.random.randint(0, 2 ** 31)

    return table, turn


def flat_game(nb_playouts, game_time_limit=100):
    hash_table, hash_turn = generate_hash_structures()
    board = Board(hash_table=hash_table, hash_turn=hash_turn)

    figures = [board.display()]
    while not board.over and board.game_time < game_time_limit:
        dice_score = random.randint(1, MAX_DICE)
        best_move = flat(board, dice_score, nb_playouts)
        board.play(best_move)
        figures.append(board.display())
        print('game_time :', board.game_time)

    return figures


def UCB_game(nb_playouts, game_time_limit=100):
    hash_table, hash_turn = generate_hash_structures()
    board = Board(hash_table=hash_table, hash_turn=hash_turn)

    figures = [board.display('names')]
    while not board.over and board.game_time < game_time_limit:
        dice_score = random.randint(1, MAX_DICE)
        best_move = UCB(board, dice_score, nb_playouts)
        board.play(best_move)
        figures.append(board.display('names'))
        print('game_time :', board.game_time)
    return figures


def UCT_game(nb_playouts, game_time_limit=100, save_gif=True):
    hash_table, hash_turn = generate_hash_structures()
    board = Board(hash_table=hash_table, hash_turn=hash_turn)

    figures = []
    if save_gif is True:
        figures = [board.display()]
    while not board.over and board.game_time < game_time_limit:
        dice_score = random.randint(1, board.map.max_dice)
        best_move = best_move_UCT(board, dice_score, nb_playouts, c=0.6)
        board.play(best_move)
        if save_gif is True:
            figures.append(board.display('names'))
        print('game_time :', board.game_time)
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


if __name__ == '__main__':
    print('Debut')


    b = Board(*generate_hash_structures(), mapp=Map("P32-D3-S48-v1"))

    plot_fig(b.display('names'))





