import os
import pickle
import sys

import numpy as np
import random
import copy
import pprint
from src.board import Board
from src.map import Map
from src.utils import *
from src.algos import flat, UCB, best_move_UCT, best_move_RAVE, best_move_GRAVE, best_move_UCT_pas_MAST

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
    table = dict(zip(keys, np.random.randint(0, 2 ** 31, (nb_cases, b.map.nb_players + 1))))

    turn = {RED: np.random.randint(0, 2 ** 31),
            BLUE: np.random.randint(0, 2 ** 31),
            GREEN: np.random.randint(0, 2 ** 31)}

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
        print('game_time :', board.game_time, f'({round(end_time - start_time, 2)}s)')
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
            print('Vous avez joué ' + chosen_move.__str__())
        else:
            print('\n\n-----------------------------------\n\n')
            print('A BLUE de jouer !')

            best_move = best_move_UCT(b_test, dice_score, nb_playouts, c=0.6)
            figures.append(b_test.display('names'))
            plot_fig(figures[-1])
            b_test.play(best_move[0], best_move[1])
            print('game_time :', b_test.game_time)
    return figures


def UCT_vs_UCT(board: Board, nb_playouts, nb_games, save_gif=False):
    sum_wins = {RED: 0, BLUE: 0}

    red_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    red_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    blue_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    blue_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    if board.map.nb_players == 3:
        sum_wins[GREEN] = 0
    for g in range(nb_games):
        figures = []
        b_cop = board.copy()
        print("Game " + str(g + 1))
        start_time = time.perf_counter()
        if save_gif is True and g <= 4:
            figures.append(b_cop.display('names'))
        print("Game_time : ", end="")
        while not b_cop.over:
            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")

            dice_score = random.randint(1, board.map.max_dice)
            b_cop.transposition_table.playouts_MAST = red_MAST_playouts
            b_cop.transposition_table.win_MAST = red_MAST_wins
            chosen_move_red = best_move_UCT(b_cop, dice_score, nb_playouts, mode=1, c=0.4, mast_param=0.25)
            b_cop.play(chosen_move_red)
            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")
            if save_gif is True and g <= 4:
                figures.append(b_cop.display('names'))
            if b_cop.over:
                break

            dice_score = random.randint(1, board.map.max_dice)
            b_cop.transposition_table.playouts_MAST = blue_MAST_playouts
            b_cop.transposition_table.win_MAST = blue_MAST_wins
            chosen_move_blue = best_move_UCT(b_cop, dice_score, nb_playouts, mode=1, c=0.4, mast_param=0.5)
            b_cop.play(chosen_move_blue)
            if save_gif is True and g <= 4:
                figures.append(b_cop.display('names'))
        end_time = time.perf_counter()

        sum_wins[b_cop.winner] += 1
        print(f"- game_time : {b_cop.game_time} - ({round((end_time - start_time) / 60, 0)}min)")
        print("WINS : ")
        print("RED  -  BLUE")
        pprint.pprint(sum_wins)
        if save_gif is True and g <= 4:
            figs2gif(figures, name=f"2p_{nb_playouts}plyt_game{g + 1}.gif")


        with open(f"sum_wins_{nb_playouts}plyt_{g}games.pkl", "wb") as f:
            pickle.dump(sum_wins, f)
        # with open(f"transposition_table.pkl", "wb") as f:
        #     pickle.dump(board.transposition_table, f)


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

def RAVE_vs_RAVE(board: Board, nb_playouts, nb_games, beta1, beta2, save_gif=False):
    sum_wins = {RED: 0, BLUE: 0}
    red_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    red_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    blue_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    blue_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    for g in range(nb_games):
        figures = []
        b_cop = board.copy()
        print("Game " + str(g + 1) + f" RAVE{beta1}_vs_RAVE{beta2}")
        start_time = time.perf_counter()
        if save_gif is True:
            figures.append(b_cop.display('names'))

        while not b_cop.over:
            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-")

            dice_score = random.randint(1, board.map.max_dice)
            board.transposition_table.playouts_MAST = red_MAST_playouts
            board.transposition_table.win_MAST = red_MAST_wins
            chosen_move_red = best_move_RAVE(b_cop, dice_score,
                                             nb_playouts,
                                             mode=1,
                                             mast_param=0.25,
                                             beta_param=beta1)
            b_cop.play(chosen_move_red)

            if save_gif is True:
                figures.append(b_cop.display('names'))
            if b_cop.over:
                break

            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-")
            dice_score = random.randint(1, board.map.max_dice)
            board.transposition_table.playouts_MAST = blue_MAST_playouts
            board.transposition_table.win_MAST = blue_MAST_wins
            chosen_move_blue = best_move_RAVE(b_cop,
                                              dice_score,
                                              nb_playouts,
                                              mode=1,
                                              mast_param=0.25,
                                              beta_param=beta2)
            b_cop.play(chosen_move_blue)
            if save_gif is True:
                figures.append(b_cop.display('names'))

        end_time = time.perf_counter()

        sum_wins[b_cop.winner] += 1
        print(f" game_time : {b_cop.game_time} - ({round((end_time - start_time) / 60, 0)}min)")
        print("WINS : ")
        print("RED  -  BLUE")
        pprint.pprint(sum_wins)
        if save_gif is True:
            figs2gif(figures,
                     name=f"RAVExRAVE_{nb_playouts}plyt_game{g + 1}_pid{os.getpid()}.gif")

        with open(f"sum_wins_{nb_playouts}plyt_RAVExRAVE_{g + 1}games_pid{os.getpid()}.pkl",
                  "wb") as f:
            pickle.dump(sum_wins, f)

def RAVE_vs_UCT(board: Board, nb_playouts, nb_games, save_gif=False):
    sum_wins = {RED: 0, BLUE: 0}

    red_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    red_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    blue_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    blue_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    for g in range(nb_games):
        figures = []
        b_cop = board.copy()
        print("Game " + str(g + 1))
        start_time = time.perf_counter()
        if save_gif is True and g <= 4:
            figures.append(b_cop.display('names'))
        print("Game_time : ", end="")
        while not b_cop.over:
            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")

            dice_score = random.randint(1, board.map.max_dice)
            b_cop.transposition_table.playouts_MAST = red_MAST_playouts
            b_cop.transposition_table.win_MAST = red_MAST_wins
            chosen_move_red = best_move_RAVE(b_cop, dice_score, nb_playouts, mode=1, mast_param=0.2)
            b_cop.play(chosen_move_red)
            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")
            if save_gif is True and g <= 4:
                figures.append(b_cop.display('names'))
            if b_cop.over:
                break

            dice_score = random.randint(1, board.map.max_dice)
            b_cop.transposition_table.playouts_MAST = blue_MAST_playouts
            b_cop.transposition_table.win_MAST = blue_MAST_wins
            chosen_move_blue = best_move_UCT(b_cop, dice_score, nb_playouts, mode=1, c=0.4, mast_param=0.2)
            b_cop.play(chosen_move_blue)
            if save_gif is True and g <= 4:
                figures.append(b_cop.display('names'))
        end_time = time.perf_counter()

        sum_wins[b_cop.winner] += 1
        print(f"- game_time : {b_cop.game_time} - ({round((end_time - start_time) / 60, 0)}min)")
        print("WINS : ")
        print("RED  -  BLUE")
        pprint.pprint(sum_wins)
        if save_gif is True and g <= 4:
            figs2gif(figures, name=f"RAVExUCT_{nb_playouts}plyt_game{g + 1}_pid{os.getpid()}.gif")

        with open(f"sum_wins_{nb_playouts}plyt_{g}games_pid{os.getpid()}.pkl", "wb") as f:
            pickle.dump(sum_wins, f)
        # with open(f"transposition_table.pkl", "wb") as f:
        #     pickle.dump(board.transposition_table, f)

def RAVE_vs_UCT_vs_UCT(board, nb_playouts, nb_games, save_gif=False):
    sum_wins = {RED: 0, BLUE: 0}
    if board.map.nb_players == 3:
        sum_wins[GREEN] = 0
    for g in range(nb_games):
        figures = []
        b_cop = board.copy()
        print("Game " + str(g + 1) + " RAVE_vs_UCT_vs_UCT")
        start_time = time.perf_counter()
        if save_gif is True:
            figures.append(b_cop.display('names'))

        while not b_cop.over:
            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")
            dice_score = random.randint(1, board.map.max_dice)
            chosen_move_red = best_move_RAVE(b_cop, dice_score, nb_playouts, mode=1)
            b_cop.play(chosen_move_red)

            if save_gif is True and g <= 4:
                figures.append(b_cop.display('names'))
            if b_cop.over:
                break

            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")
            dice_score = random.randint(1, board.map.max_dice)
            chosen_move_blue = best_move_UCT(b_cop, dice_score, nb_playouts, mode=1)
            b_cop.play(chosen_move_blue)
            if save_gif is True and g <= 4:
                figures.append(b_cop.display('names'))
            if b_cop.over:
                break

            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")
            dice_score = random.randint(1, board.map.max_dice)
            chosen_move_blue = best_move_UCT(b_cop, dice_score, nb_playouts, mode=1)
            b_cop.play(chosen_move_blue)
            if save_gif is True and g <= 4:
                figures.append(b_cop.display('names'))
            if b_cop.over:
                break

        end_time = time.perf_counter()

        sum_wins[b_cop.winner] += 1
        print(f" game_time : {b_cop.game_time} - ({round((end_time - start_time) / 60, 0)}min)")
        print("WINS : ")
        print("RED  -  BLUE  -  GREEN")
        pprint.pprint(sum_wins)
        if save_gif is True and g <= 4:
            figs2gif(figures, name=f"RAVE-UCT-UCT_{nb_playouts}plyt_game{g + 1}.gif")

        board.transposition_table.win_MAST = b_cop.transposition_table.win_MAST
        board.transposition_table.playouts_MAST = b_cop.transposition_table.playouts_MAST

        with open(f"sum_wins_{nb_playouts}plyt_{g}games.pkl", "wb") as f:
            pickle.dump(sum_wins, f)
        with open(f"transposition_table.pkl", "wb") as f:
            pickle.dump(board.transposition_table, f)


def GRAVE_game(board: Board, nb_playouts, game_time_limit, treshold, mode, save_gif=False):
    figures = []
    if save_gif is True:
        figures = [board.display('names')]
    while not board.over and board.game_time < game_time_limit:

        dice_score = random.randint(1, board.map.max_dice)
        start_time = time.perf_counter()
        best_move = best_move_GRAVE(board, dice_score, nb_playouts, treshold=20, mode=mode)
        end_time = time.perf_counter()
        board.play(best_move)
        if save_gif is True:
            figures.append(board.display('names'))
        print('game_time :', board.game_time, f'({round(end_time - start_time, 2)}s)')
    if save_gif is True:
        return figures

def GRAVE_vs_GRAVE(board: Board, nb_playouts, nb_games, treshold1, treshold2, save_gif=False):
    sum_wins = {RED: 0, BLUE: 0}
    red_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    red_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    blue_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    blue_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    for g in range(nb_games):
        figures = []
        b_cop = board.copy()
        print("Game " + str(g + 1) + f" GRAVE{treshold1}_vs_GRAVE{treshold2}")
        start_time = time.perf_counter()
        if save_gif is True:
            figures.append(b_cop.display('names'))

        while not b_cop.over:
            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-")

            dice_score = random.randint(1, board.map.max_dice)
            board.transposition_table.playouts_MAST = red_MAST_playouts
            board.transposition_table.win_MAST = red_MAST_wins
            chosen_move_red = best_move_GRAVE(b_cop, dice_score, nb_playouts, treshold=treshold1, mode=1, mast_param=0.25)
            b_cop.play(chosen_move_red)

            if save_gif is True:
                figures.append(b_cop.display('names'))
            if b_cop.over:
                break

            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-")
            dice_score = random.randint(1, board.map.max_dice)
            board.transposition_table.playouts_MAST = blue_MAST_playouts
            board.transposition_table.win_MAST = blue_MAST_wins
            chosen_move_blue = best_move_GRAVE(b_cop, dice_score, nb_playouts, treshold=treshold2, mode=1, mast_param=0.25)
            b_cop.play(chosen_move_blue)
            if save_gif is True:
                figures.append(b_cop.display('names'))

        end_time = time.perf_counter()

        sum_wins[b_cop.winner] += 1
        print(f" game_time : {b_cop.game_time} - ({round((end_time - start_time) / 60, 0)}min)")
        print("WINS : ")
        print("RED  -  BLUE")
        pprint.pprint(sum_wins)
        if save_gif is True:
            figs2gif(figures, name=f"GRAVE{treshold1}xGRAVE{treshold2}_{nb_playouts}plyt_game{g + 1}_pid{os.getpid()}.gif")

        with open(f"sum_wins_{nb_playouts}plyt_GRAVE{treshold1}xGRAVE{treshold2}_{g+1}games_pid{os.getpid()}.pkl", "wb") as f:
            pickle.dump(sum_wins, f)

def RAVE_vs_GRAVE(board, nb_playouts, nb_games, treshold, save_gif=False):
    sum_wins = {RED: 0, BLUE: 0}
    red_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    red_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    blue_MAST_wins = copy.deepcopy(board.transposition_table.win_MAST)
    blue_MAST_playouts = copy.deepcopy(board.transposition_table.playouts_MAST)

    for g in range(nb_games):
        figures = []
        b_cop = board.copy()
        print("Game " + str(g + 1) + " RAVE_vs_GRAVE")
        start_time = time.perf_counter()
        if save_gif is True:
            figures.append(b_cop.display('names'))

        while not b_cop.over:
            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")

            dice_score = random.randint(1, board.map.max_dice)
            board.transposition_table.playouts_MAST = red_MAST_playouts
            board.transposition_table.win_MAST = red_MAST_wins
            chosen_move_red = best_move_RAVE(b_cop, dice_score, nb_playouts, mode=1, mast_param=0.25)
            b_cop.play(chosen_move_red)

            if save_gif is True:
                figures.append(b_cop.display('names'))
            if b_cop.over:
                break

            if b_cop.game_time % 5 == 0:
                print(f"{b_cop.game_time}-", end="")
            dice_score = random.randint(1, board.map.max_dice)
            board.transposition_table.playouts_MAST = blue_MAST_playouts
            board.transposition_table.win_MAST = blue_MAST_wins
            chosen_move_blue = best_move_GRAVE(b_cop, dice_score, nb_playouts, treshold=treshold, mode=1, mast_param=0.25)
            b_cop.play(chosen_move_blue)
            if save_gif is True:
                figures.append(b_cop.display('names'))

        end_time = time.perf_counter()

        sum_wins[b_cop.winner] += 1
        print(f" game_time : {b_cop.game_time} - ({round((end_time - start_time) / 60, 0)}min)")
        print("WINS : ")
        print("RED  -  BLUE")
        pprint.pprint(sum_wins)
        if save_gif is True:
            figs2gif(figures, name=f"RAVE-UCT-UCT_{nb_playouts}plyt_game{g+1}_pid{os.getpid()}.gif")

        with open(f"sum_wins_{nb_playouts}plyt_RAVExGRAVE_{g+1}games_pid{os.getpid()}.pkl", "wb") as f:
            pickle.dump(sum_wins, f)


if __name__ == '__main__':
    print('Debut')

    nb_playouts = 8000

    s3 = Board.get_situation_3(*generate_hash_structures(REF3))

    plot_fig(s3.display('names'))

    for i in range(10):
        s1 = Board.get_situation_1(*generate_hash_structures(REF3))
        s2 = Board.get_situation_2(*generate_hash_structures(REF3))
        s3 = Board.get_situation_3(*generate_hash_structures(REF3))

        best_move_s1 = best_move_RAVE(s1, 1, nb_playouts, mode=2, mast_param=0.2, beta_param=1e-3)
        s1.transposition_table.table = {}
        best_move_s2 = best_move_RAVE(s2, 1, nb_playouts, mode=2, mast_param=0.2, beta_param=1e-3)
        s2.transposition_table.table = {}
        best_move_s3 = best_move_RAVE(s3, 2, nb_playouts, mode=2, mast_param=0.2, beta_param=1e-3)
        s3.transposition_table.table = {}

        print(i,": Best move s1 :", best_move_s1)
        print(i,": Best move s2 :", best_move_s2)
        print(i,": Best move s3 :", best_move_s3)

    print("Fin")
