import pickle
import time
import unittest
import random
from unittest import skip

import numpy as np
from matplotlib import pyplot as plt

from src.map import Map
from src.move import Move
from src.board import Board
from src.table import Table
from main import generate_hash_structures
from src.utils import plot_fig

BLOCK = 0
RED = 1
BLUE = 2
GREEN = 3
EMPTY = 4
GOAL = -1

REF2 = "P22-D3-S34-v1"
REF3 = "P32-D3-S48-v1"

class TestHashcode(unittest.TestCase):

    def setUp(self):
        hash_table, hash_turn = generate_hash_structures("P22-D3-S34-v1")
        self.hash_table = hash_table
        self.hash_turn = hash_turn

    def test_HashCodes_1(self):
        # Il me faut un move et son inverse et je suis censé retomber sur le même hashcode
        b = Board(hash_table=self.hash_table, hash_turn=self.hash_turn, mapp=Map("P22-D3-S34-v1"))
        b.change_content('d1', RED)
        b.change_content('g1', BLUE)
        b.piece_pools[RED][1] = 1
        b.piece_pools[BLUE][1] = 1

        m1 = Move(RED, 'd1', 'd2', b.get_content('d2'), ['d1', 'd2'], 1)
        m2 = Move(BLUE, 'f1', 'f2', b.get_content('f2'), ['f1', 'f2'], 1)

        self.assertTrue(m1.is_valid(b))
        self.assertEqual(m1.__str__(), 'RED move : 1(d1,d2)')
        self.assertEqual(b.hashcode, 0)

        b.play(m1)
        b.play(m2)

        m1_reverse = Move(RED, 'd2', 'd1', b.get_content('d1'), ['d2', 'd1'], 1)
        m2_reverse = Move(BLUE, 'f2', 'f1', b.get_content('f1'), ['f2', 'f1'], 1)

        b.play(m1_reverse)
        b.play(m2_reverse)

        self.assertEqual(b.hashcode, 0)

    def test_HashCode_2(self):
        # Il faut que j'essaie de faire le scénario où un pion revient dans son pool
        # Je vais utiliser des moves qui sont pas vraiment légaux (tp des pions)

        b = Board(hash_table=self.hash_table, hash_turn=self.hash_turn)

        m1 = Move(RED, 'a0', 'e3', b.get_content('e3'), ['pas', 'important'], -1)

        self.assertEqual(b.hashcode, 0)

        b.play(m1)
        hash1 = b.hashcode

        m2 = Move(BLUE, 'i0', 'e3', b.get_content('e3'), ['pas', 'important'], -1)

        b.play(m2)

        m1 = Move(RED, 'a0', 'e3', b.get_content('e3'), ['pas', 'important'], -1)

        b.play(m1)

        hash2 = b.hashcode

        self.assertEqual(hash1, hash2)

    def test_HashCode_3(self):
        # On teste le bon fonctionnement des hashcodes lorsqu'on touche à des blocks

        b = Board(hash_table=self.hash_table, hash_turn=self.hash_turn)

        b.change_content('c4', RED)
        b.piece_pools[RED][1] -= 1

        m1 = Move(RED, 'c4', 'b3', b.get_content('b3'), ['c4', 'c3', 'b3'], 2)
        m1.chosen_placement = 'c4'
        self.assertTrue(m1.is_valid(b))  # Ca va vérifier que le move est bien valide ET ça va calculer les
        # destinations possibles pour le block.

        self.assertEqual(set(m1.block_placements),
                         {'b2', 'd2', 'f2', 'h2', 'c3', 'e3', 'g3', 'c4', 'e4', 'g4', 'c5', 'd5', 'f5', 'g5', 'e6',
                          'e7', 'e8'})

        hash1 = b.hashcode

        b.play(m1)

        m1_reverse = Move(RED, 'b3', 'c4', b.get_content('c4'), ['b3', 'c3', 'c4'], 2)
        m1_reverse.chosen_placement = 'b3'

        self.assertEqual(b.get_content('c4'), BLOCK)
        self.assertTrue(m1_reverse.is_valid(b))
        b.play(m1_reverse)

        hash2 = b.hashcode

        self.assertEqual(hash1, hash2)


class TestMove(unittest.TestCase):

    def setUp(self):
        self.map = Map("P22-D3-S34-v1")
        self.b = Board(mapp=self.map)
        self.table = Table(mapp=self.map)

    def test_code(self):
        self.b.change_content('c5', RED)
        self.b.change_content('a0', EMPTY)

        self.b.piece_pools[RED][1] = 0

        self.b.change_content('e5', BLUE)
        self.b.change_content('h1', BLUE)
        self.b.change_content('i0', EMPTY)

        self.b.piece_pools[BLUE][1] = 0

        self.b.change_content('e7', BLOCK)
        self.b.change_content('c4', BLOCK)

        self.b.turn = BLUE

        blue_moves = self.b.valid_moves(2)

        self.b.turn = RED

        red_moves = self.b.valid_moves(2)

        self.assertTrue(len(red_moves) == 1)

        red_code1 = red_moves[0].code(self.map)

        self.b.change_content('c4', EMPTY)
        self.b.change_content('c3', BLOCK)

        red_moves = self.b.valid_moves(2)

        red_code2 = red_moves[-1].code(self.map)  # Normalement les coups sont toujours renvoyés dans le même ordre.

        self.assertEqual(red_code1, red_code2)

        biggest_code = blue_moves[-1].code(self.map)

        self.assertGreater(self.map.nb_possible_moves, biggest_code)

        b2 = Board()
        b2.change_content('c5', RED)
        b2.change_content('e5', BLUE)

        artificial_move = Move(RED, 'c5', 'e5', BLUE, ['c5', 'd5', 'e5'], 2)

        self.assertEqual(artificial_move.code(self.map), red_code1)


class TestBoard2Players(unittest.TestCase):

    def setUp(self):

        hash_table, hash_turn = generate_hash_structures(map_reference="P22-D3-S34-v1")
        self.hash_table = hash_table
        self.hash_turn = hash_turn
        self.b = Board(hash_table=self.hash_table, hash_turn=self.hash_turn)
        with open('table_test_2player.pkl', 'rb') as f:
            self.b.transposition_table = pickle.load(f)

    def test_valid_moves(self):
        """
        Ca va servir à vérifier que les moves sont bien générés dans le même ordre à chaque fois
        """
        # On va jouer 30 coups aléatoires pour avoir un plateau aléatoire
        for i in range(30):
            moves = self.b.valid_moves(random.randint(1,3))
            self.b.play(random.choice(moves))

        moves = self.b.valid_moves(3)

        b_bis = Board(*generate_hash_structures(map_reference="P22-D3-S34-v1"), mapp=Map('P22-D3-S34-v1'))
        for n, data in self.b.board.nodes(data=True):
            b_bis.change_content(n, data["content"])

        moves_bis = b_bis.valid_moves(3)

        self.assertEqual(len(moves), len(moves_bis))

        for i in range(len(moves)):
            self.assertEqual(str(moves[i]), str(moves_bis[i]))

    def test_playout_policy_2(self):
        # La on essaie d'observer les probas pour la deuxième méthode de playout
        self.b.change_content("e5", RED)
        self.b.piece_pools[RED][1] -= 1

        valid_moves = self.b.valid_moves(3)
        grouped_moves = self.b.get_grouped_moves(valid_moves)


        policy = self.b.get_policy(grouped_moves, 1)

        table = self.b.transposition_table

        for i, m in enumerate(grouped_moves[0]+grouped_moves[1:]):

            print(i,':',m,end=" ")

            print("Proba : "+str(policy[i]))
            # self.assertGreaterEqual(policy[-1], policy[i])

        for m in valid_moves :
            print(m,end=" - ")
            code = m.code(self.b.map)
            print(table.win_MAST[code][m.player], "/", table.playouts_MAST[code],
                  )  # , round(table.win_amaf[code]/table.playouts_amaf[code],2))

        # On va faire 100 playout et voir si on retrouve bien les bonnes stats sur les coups gagnants

        win_move_blue = Move(BLUE, 'e8', 'e9', GOAL, ['e8','e9'],1)
        win_move_red = Move(RED, 'e8', 'e9', GOAL, ['e8','e9'],1)

        self.assertEqual(table.win_MAST[win_move_blue.code(self.b.map)][RED], 0)
        self.assertEqual(table.win_MAST[win_move_red.code(self.b.map)][BLUE], 0)

        self.assertEqual(table.win_MAST[win_move_red.code(self.b.map)][RED], table.playouts_MAST[win_move_red.code(self.b.map)])
        self.assertEqual(table.win_MAST[win_move_blue.code(self.b.map)][BLUE], table.playouts_MAST[win_move_blue.code(self.b.map)])


    def test_playout_policy(self):


        self.b.change_content("e5", RED)
        self.b.piece_pools[RED][1] -= 1

        valid_moves = self.b.valid_moves(3)

        policy = self.b.get_policy(valid_moves, 0.2)

        table = self.b.transposition_table

        best_i = None
        for i, m in enumerate(valid_moves):
            if m.start_node == 'e5' and m.end_node == 'e8':
                best_i = i
            print(i,':',m,end=" ")
            code = m.code(self.b.map)
            print(table.win_MAST[code][m.player], "/", table.playouts_MAST[code], "-")#, round(table.win_amaf[code]/table.playouts_amaf[code],2))
            print("Proba : "+str(policy[i]))

        for i in range(len(valid_moves)):
            self.assertGreaterEqual(policy[best_i], policy[i])


        # On va faire 100 playout et voir si on retrouve bien les bonnes stats sur les coups gagnants

        win_move_blue = Move(BLUE, 'e8', 'e9', GOAL, ['e8','e9'],1)
        win_move_red = Move(RED, 'e8', 'e9', GOAL, ['e8','e9'],1)

        self.assertEqual(table.win_MAST[win_move_blue.code(self.b.map)][RED], 0)
        self.assertEqual(table.win_MAST[win_move_red.code(self.b.map)][BLUE], 0)

        self.assertEqual(table.win_MAST[win_move_red.code(self.b.map)][RED], table.playouts_MAST[win_move_red.code(self.b.map)])
        self.assertEqual(table.win_MAST[win_move_blue.code(self.b.map)][BLUE], table.playouts_MAST[win_move_blue.code(self.b.map)])


        # Ensuite ça peut être bien de regarder à quoi ressemblent les tirages sur les derniers coups possibles
        # sur une map que je crée. Pour voir si ça aide bien à aller vers la victoire ou pas.

        # Peut être aussi voir s'il faut que je fasse un truc ou ça tire en deux temps. D'abord le déplacement du pion,
        # et ensuite seulement si on tombe sur la barricade je tire le placement de la barricade.
        # Ca peut être vraiment bien je pense que je vais faire ça de ce pas en fait.


    def test_playout_mm(self):
        """Affiche la moyenne mobile des durées des playouts.
            On aimerait qu'elle descende au fur et à mesure que les parties sont mémorisées."""

        game_times = []
        b = Board(hash_table=self.hash_table, hash_turn=self.hash_turn)
        nb_playouts = 4000
        save_gif = False
        start_time = time.perf_counter()
        res_sum = {
            RED: 0,
            BLUE: 0
        }

        for p in range(nb_playouts):

            b_cop = b.copy()

            played = []

            if p >= nb_playouts:
                save_gif = True

            winner = b_cop.playout_MAST(played, 0.3, mode=2, save_gif=save_gif)
            # winner = b_cop.playout(mode=2)

            res_sum[winner] += 1
            game_times.append(b_cop.game_time)
            if b_cop.game_time > 600:
                print("big game time :", b_cop.game_time)
            b.update_MAST(winner, played)

            if p % 100 == 0:
                print(f'\n ----- {p} playouts ------ \n')
                print("temps :", round(time.perf_counter() - start_time,2),"s")
                start_time = time.perf_counter()

        print("Victoires RED : ", res_sum[RED])
        print("Victoires BLUE ", res_sum[BLUE])

        with open("game_times_2player.pkl", "wb") as f:
            pickle.dump(game_times, f)

        with open("table_test_2player.pkl","wb") as f:
            pickle.dump(b.transposition_table, f)

    def test_plot_mm(self):
        with open("game_times_2player.pkl", "rb") as f:
            game_times = pickle.load(f)

        mm200 = np.convolve(game_times, np.ones(200), 'valid') / 200
        mm100 = np.convolve(game_times, np.ones(100), 'valid') / 100
        mm50 = np.convolve(game_times, np.ones(50), 'valid') / 50

        # plt.plot(mm50, label="mm50")
        plt.plot(mm100, label='mm100')
        plt.plot(mm200, label='mm200')
        plt.xlabel("playout")
        plt.ylabel("game time")
        plt.legend()
        plt.show()



if __name__ == '__main__':
    unittest.main()



