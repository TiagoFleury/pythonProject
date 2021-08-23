import pickle
import unittest
import random
import time

import numpy as np
from matplotlib import pyplot as plt

from main import generate_hash_structures
from src.board import Board
from src.map import Map
from src.move import Move
from src.utils import plot_fig

BLOCK = 0
RED = 1
BLUE = 2
GREEN = 3
EMPTY = 4
GOAL = -1

REF2 = "P22-D3-S34-v1"
REF3 = "P32-D3-S48-v1"

class TestBoard3Players(unittest.TestCase):

    def setUp(self):

        hash_table, hash_turn = generate_hash_structures(map_reference="P32-D3-S48-v1")
        self.hash_table = hash_table
        self.hash_turn = hash_turn
        self.b = Board(hash_table=self.hash_table, hash_turn=self.hash_turn, mapp=Map("P32-D3-S48-v1"))
        with open('table_test_3player.pkl', 'rb') as f:
            self.b.transposition_table = pickle.load(f)

    def test_valid_moves(self):
        """
        Ca va servir à vérifier que les moves sont bien générés dans le même ordre à chaque fois
        """
        # On va jouer 30 coups aléatoires pour avoir un plateau aléatoire
        for i in range(30):
            moves = self.b.valid_moves(random.randint(1, 3))
            self.b.play(random.choice(moves))

        moves = self.b.valid_moves(3)

        plot_fig(self.b.display('names'))

        b_bis = Board(*generate_hash_structures(map_reference="P32-D3-S48-v1"), mapp=Map('P32-D3-S48-v1'))
        for n, data in self.b.board.nodes(data=True):
            b_bis.change_content(n, data["content"])

        moves_bis = b_bis.valid_moves(3)

        self.assertEqual(len(moves), len(moves_bis))

        for i in range(len(moves)):
            self.assertEqual(str(moves[i]), str(moves_bis[i]))

    def test_playout_policy(self):


        self.b.change_content("e5", RED)
        self.b.piece_pools[RED][1] -= 1

        valid_moves = self.b.valid_moves(3)

        policy = self.b.get_policy(valid_moves, 0.2)

        table = self.b.transposition_table

        for i, m in enumerate(valid_moves):

            print(i,':',m,end=" ")
            code = m.code(self.b.map)
            print(table.win_MAST[code][m.player], "/", table.playouts_MAST[code], "-")#, round(table.win_amaf[code]/table.playouts_amaf[code],2))
            print("Proba : "+str(policy[i]))
            self.assertGreaterEqual(policy[-1], policy[i])


        win_move_blue = Move(BLUE, 'e8', 'e9', GOAL, ['e8','e9'], 1)
        win_move_red = Move(RED, 'e8', 'e9', GOAL, ['e8','e9'], 1)
        win_move_green = Move(GREEN, 'e8', 'e9', GOAL, ['e8', 'e9'], 1)


        # Les autres joueurs ne sont pas censés gagner de parties après ce coup
        self.assertEqual(table.win_MAST[win_move_blue.code(self.b.map)][RED], 0)
        self.assertEqual(table.win_MAST[win_move_red.code(self.b.map)][BLUE], 0)
        self.assertEqual(table.win_MAST[win_move_green.code(self.b.map)][BLUE], 0)

        #Tous ces coups sont gagants donc il doit y avoir autant de wins que de playouts joués à partir de ce coup.
        self.assertEqual(table.win_MAST[win_move_red.code(self.b.map)][RED],
                         table.playouts_MAST[win_move_red.code(self.b.map)])
        self.assertEqual(table.win_MAST[win_move_blue.code(self.b.map)][BLUE],
                         table.playouts_MAST[win_move_blue.code(self.b.map)])
        self.assertEqual(table.win_MAST[win_move_green.code(self.b.map)][GREEN],
                         table.playouts_MAST[win_move_green.code(self.b.map)])

    def test_playout_mm(self):
        """
        Fait un certain nombre de playouts pour remplir la table de transposition et sauvegarder la durée des parties
        On aimerait qu'elles baissent au fur et à mesure que la table AMAF est remplie."""

        game_times = []
        b = Board(hash_table=self.hash_table, hash_turn=self.hash_turn, mapp=Map(REF3))
        nb_playouts = 1000
        save_gif = False
        start_time = time.perf_counter()
        res_sum = {
            RED: 0,
            BLUE: 0,
            GREEN: 0
        }

        for p in range(nb_playouts):

            b_cop = self.b.copy()

            played = []

            if p >= nb_playouts:
                save_gif = True

            winner = b_cop.playout_MAST(played, 0.5, mode=2, save_gif=save_gif)
            # winner = b_cop.playout(mode=2)
            res_sum[winner] += 1
            game_times.append(b_cop.game_time)
            if b_cop.game_time > 600:
                print("big game time :", b_cop.game_time)
            # b.update_table(winner, played)

            if p % 100 == 0:
                print(f'\n ----- {p} playouts ------ \n')
                print("temps :", round(time.perf_counter() - start_time,2),"s")
                start_time = time.perf_counter()

        print("Victoires RED :", res_sum[RED])
        print("Victoires BLUE :", res_sum[BLUE])
        print("Victoires GREEN :", res_sum[GREEN])


        with open("game_times_3player.pkl", "wb") as f:
            pickle.dump(game_times, f)

        # with open("table_test_3player.pkl","wb") as f:
        #     pickle.dump(b.transposition_table, f)

    def test_plot_mm(self):
        '''
        Juste pour afficher la moyenne mobile
        '''
        with open("game_times_3player.pkl", "rb") as f:
            game_times = pickle.load(f)

        mm300 = np.convolve(game_times, np.ones(300), 'valid') / 300
        mm100 = np.convolve(game_times, np.ones(100), 'valid') / 100
        mm50 = np.convolve(game_times, np.ones(50), 'valid') / 50

        # plt.plot(mm50, label="mm50")
        plt.plot(mm100, label='mm100')
        plt.plot(mm300, label='mm300')
        plt.legend()
        plt.show()

if __name__ == '__main__':
    unittest.main()
