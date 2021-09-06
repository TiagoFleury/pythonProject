import copy
import math
import time

import numpy as np

from src.map import Map
from src.move import Move
from src.utils import timeit, figs2gif
from src.table import Table
import networkx as nx
import random
import matplotlib.pyplot as plt
from typing import Union, List

BLOCK = 0
RED = 1
BLUE = 2
GREEN = 3
EMPTY = 4
GOAL = -1

REF2 = "P22-D3-S34-v1"
REF3 = "P32-D3-S48-v1"

INT2STRING = {RED: 'RED', BLUE: 'BLUE', GREEN: 'GREEN'}

MAX_DICE = 3


class Board:

    def __init__(self, hash_table=None, hash_turn=None, mapp=Map("P22-D3-S34-v1")):

        self.hashcode = 0

        if mapp.reference == "P22-D3-S34-v1":
            self.piece_pools = {RED: ['a0', 2], BLUE: ['i0', 2]}
            self.opponents = {RED: [BLUE],

                              BLUE: [RED]}
        elif mapp.reference == "P32-D3-S48-v1":
            self.piece_pools = {RED: ['a0', 2], BLUE: ['i0', 2], GREEN: ['e0', 2]}
            self.opponents = {
                RED: [GREEN, BLUE],
                GREEN: [RED, BLUE],
                BLUE: [GREEN, RED]
            }

        self.turn = RED

        self.game_time = 0

        self.over = False

        self.winner = None  # On utilisera un dictionnaire pour stocker les victoires des joueurs

        self.hash_table = hash_table
        self.hash_turn = hash_turn

        self.transposition_table = Table(mapp)

        self.map = mapp
        self.board = mapp.get_board()

    def next(self):
        if self.map.reference == "P22-D3-S34-v1":
            if self.turn == RED:
                return BLUE
            elif self.turn == BLUE:
                return RED

        elif self.map.reference == "P32-D3-S48-v1":
            if self.turn == RED:
                return GREEN
            elif self.turn == GREEN:
                return BLUE
            elif self.turn == BLUE:
                return RED

    def get_content(self, node_name):
        return self.board.nodes[node_name]['content']

    def change_content(self, node_name, new_content):
        if new_content not in [RED, BLUE, GREEN, BLOCK, GOAL, EMPTY]:
            print("Mauvaise valeur pour 'content' !, vous avez placé : ", new_content)
            raise BaseException
        else:
            self.board.nodes[node_name]['content'] = new_content

    def look_table(self):
        return self.transposition_table.look(self)

    def new_table_entry(self, amaf: bool):
        self.transposition_table.add(self, amaf)

    def valid_moves(self, dice_score):
        """
        En fonction du score obtenu au dé, on veut récupérer l'ensemble des actions possibles. (le plus rapidement possible)
        """
        # On a un ensemble d'actions possibles par pion de la couleur à qui c'est le tour de jouer

        # On commence par récupérer les cases contenant un pion de la couleur
        nodes_containing_pieces = [node for node, data in self.board.nodes(data=True) if data['content'] == self.turn]

        valid_moves = []
        for piece in nodes_containing_pieces:
            # Récupération de tous les chemins de taille <= dice_score qui partent de piece
            target_paths = nx.single_source_shortest_path(self.board, piece, cutoff=dice_score)

            for (target, path) in target_paths.items():
                if len(path) == dice_score + 1:
                    move = Move(player=self.turn,
                                start_node=path[0],
                                end_node=target,
                                content_end_node=self.board.nodes[target]['content'],
                                path=path,
                                dice_score=dice_score)

                    if move.is_valid(self):
                        # Une fois que le move est validé, il faut spécifier où envoyer le block si c'est nécessaire

                        if move.block is False:
                            valid_moves.append(move)
                        else:
                            for placement in move.block_placements:
                                cop = move.copy()
                                cop.chosen_placement = placement
                                valid_moves.append(cop)

        return valid_moves

    def play(self, move: Union[Move, None]):  # On joue le coup et on modifie le hashcode en fonction.

        if move is not None:  # le move peut valoir None lorsqu'il n'y a pas de coup possible.
            # On commence par enlever la pièce qui bouge de sa place de départ.
            if move.block and move.chosen_placement is None:
                print("Erreur : pas de destination spécifiée pour le block")
                return 1

            if move.start_node[1] == '0':  # Si le move est initié d'un pool
                # On met d'abord correctement à jour le hashcode avec le nombre de pièce présentes dans le pool.
                self.hashcode = self.hashcode ^ self.hash_table[move.start_node][self.piece_pools[self.turn][1]]
                self.piece_pools[self.turn][1] -= 1  # Qu'on décrémente ensuite

                if self.piece_pools[self.turn][1] == 0:
                    self.change_content(move.start_node, EMPTY)
            else:
                self.change_content(move.start_node, EMPTY)

                # On retire donc le hashcode de la pièce de départ
                self.hashcode = self.hashcode ^ self.hash_table[move.start_node][move.player]

            # S'il y a une pièce de l'adversaire à l'arrivée on l'enlève également

            opponent_color = self.opponents[move.player]

            if move.content_end_node == GOAL:
                self.over = True
                self.winner = self.turn

            if move.content_end_node in opponent_color:
                opponent_pool_node = self.piece_pools[move.content_end_node][0]
                # On enlève la pièce
                self.change_content(move.end_node, EMPTY)  # Ligne possiblement inutile
                # On actualise le hash_code
                self.hashcode = self.hashcode ^ self.hash_table[move.end_node][move.content_end_node]
                if move.content_end_node not in opponent_color:
                    print("Bizarre, la valeur de move.content_end_node a changé")
                # Puis on replace la pièce dans son pool
                self.piece_pools[move.content_end_node][
                    1] += 1  # On incrémente le nombre de pièces présentes dans le pool
                # On actualise le hashcode en utilisant cette valeur

                self.hashcode = self.hashcode ^ self.hash_table[opponent_pool_node][
                    self.piece_pools[move.content_end_node][1]]

                self.change_content(opponent_pool_node, move.content_end_node)  # On met une pièce sur la case.

            if move.block:  # Si c'est un coup qui déplace un block.

                # On enlève le BLOCK
                self.change_content(move.end_node, EMPTY)  # Ligne possiblement inutile également
                self.hashcode = self.hashcode ^ self.hash_table[move.end_node][BLOCK]

                # Ensuite il faut replacer le block quelque part

                self.change_content(move.chosen_placement, BLOCK)

                # Cette case sera forcément vide, on peut mettre directement un BLOCK dedans
                self.hashcode = self.hashcode ^ self.hash_table[move.chosen_placement][BLOCK]

            # Enfin, il faut placer la pièce du joueur et actualiser une dernière fois le hashcode

            self.change_content(move.end_node, move.player)
            self.hashcode = self.hashcode ^ self.hash_table[move.end_node][move.player]

        # On termine le tour en changeant de tour et en modifiant le hash_turn correctement
        # Ce n'est plus le tour du joueur qui vient de jouer
        self.hashcode = self.hashcode ^ self.hash_turn[self.turn]
        # On récupère la couleur du prochain joueur
        self.turn = self.next()
        # Et c'est maintenant à son tour de jouer
        self.hashcode = self.hashcode ^ self.hash_turn[self.turn]

        self.game_time += 1

        return 0

    def playout(self, mode=1):
        """
        Fonction qui joue aléatoirement une partie à partir de l'état actuel et qui retourne le résultat.
        :param mode : Si mode=1, on tire aléatoirement sur tous les coups. Si mode=2, on tire aléatoirement
        dans un premier temps le déplacement du pion et dans un second temps la destination de la barricade
        s'il y en a une qui a été prise.
        """
        if mode == 1:
            while not self.over:
                valid_moves = self.valid_moves(random.randint(1, self.map.max_dice))  # Récupération des moves valides
                if len(valid_moves) != 0:
                    chosen_move = random.choice(valid_moves)
                    self.play(chosen_move)
                else:
                    # Dans ce cas, il n'y a pas de coup jouable
                    self.play(None)  # On passe son tour.

            return self.winner
        elif mode == 2:
            lost_time = 0
            while not self.over:
                valid_moves = self.valid_moves(random.randint(1, self.map.max_dice))
                start = time.perf_counter()
                grouped_moves = self.get_grouped_moves(valid_moves)
                end = time.perf_counter()
                lost_time += (end - start)
                if len(valid_moves) != 0:
                    chosen_group = random.choice(grouped_moves[0] + grouped_moves[1:])
                    if type(chosen_group) is list:
                        chosen_move = random.choice(chosen_group)
                    else:
                        chosen_move = chosen_group
                    self.play(chosen_move)
                else:
                    self.play(None)
            # print(round(lost_time, 3))
            return self.winner

    def playout_MAST(self, played_moves_codes=None, exploration_parameter=1, mode=1, save_gif=False):

        if played_moves_codes is None:
            print("Pas de liste transmise pour le playout MAST")
            played_moves = []

        figs = []
        if save_gif is True:
            figs = [self.display('names')]

        while not self.over:

            dice_score = random.randint(1, self.map.max_dice)
            valid_moves = self.valid_moves(dice_score)

            if len(valid_moves) != 0:

                if mode == 1:
                    policy = self.get_policy(valid_moves, exploration_parameter=exploration_parameter)
                    # print("Policy :", policy,"sum:",policy.sum())
                    chosen_move = random.choices(valid_moves, policy)[0]
                elif mode == 2:
                    grouped_moves = self.get_grouped_moves(valid_moves)
                    policy = self.get_policy(grouped_moves, exploration_parameter=exploration_parameter)
                    # print("Policy :", policy,"sum:",policy.sum())

                    chosen_group = random.choices(grouped_moves[0] + grouped_moves[1:], policy)[0]
                    if type(chosen_group) is list:
                        policy = self.get_policy(chosen_group)
                        chosen_move = random.choices(chosen_group, policy)[0]
                    else:
                        chosen_move = chosen_group
                else:
                    print("Mauvais mode pour playout MAST")
                    chosen_move = None

                played_moves_codes.append(chosen_move.code(self.map))
                self.play(chosen_move)

            else:
                self.play(None)

            if save_gif is True:
                figs.append(self.display('names'))

        if save_gif is True:
            figs2gif(figs, "new_playout_gt" + str(self.game_time) + ".gif")

        return self.winner


    def get_policy(self, move_list, exploration_parameter=1):

        if type(move_list[0]) is list:  # Pour le premier tirage (sans le tirage du placement du Block)
            # move_list[0] contient tous les coups qui ne déplacent pas de blocks
            policy = np.zeros(len(move_list[0]) + len(move_list) - 1)
            for i in range(len(move_list)):
                if i == 0:  # On considère chaque coup où Block==False individuellement
                    for j, move in enumerate(move_list[0]):
                        move_code = move.code(self.map)
                        if self.transposition_table.playouts_MAST[move_code] == 0:
                            amaf_victory_rate = 0
                        else:
                            amaf_victory_rate = (self.transposition_table.win_MAST[move_code][move.player] /
                                                 self.transposition_table.playouts_MAST[move_code])
                        policy[j] = math.exp(amaf_victory_rate / exploration_parameter)
                else:  # Et on groupe tous les coups qui déplacent une barricade entre eux en faisant la moyenne de leurs
                    # stats
                    sum = 0
                    amaf_victory_rate = 0
                    for j, move in enumerate(move_list[i]):
                        move_code = move.code(self.map)
                        if self.transposition_table.playouts_MAST[move_code] == 0:
                            amaf_victory_rate = 0
                        else:
                            amaf_victory_rate = (self.transposition_table.win_MAST[move_code][move.player] /
                                                 self.transposition_table.playouts_MAST[move_code])
                        sum += amaf_victory_rate
                    mean = sum / len(move_list[i])
                    policy[len(move_list[0]) + i - 1] = math.exp(mean / exploration_parameter)
            return policy / policy.sum()

        else:  # Si c'est simplement une liste de moves qui est fournie, on retourne juste la policy sur ces coups

            policy = np.zeros(len(move_list))

            for i, move in enumerate(move_list):
                move_code = move.code(self.map)
                # On fait la somme des exp des taux de victoire AMAF pour préparer
                # la politique de tirage des coups
                if self.transposition_table.playouts_MAST[move_code] == 0:
                    amaf_victory_rate = 0
                else:
                    amaf_victory_rate = self.transposition_table.win_MAST[move_code][move.player]
                    amaf_victory_rate /= self.transposition_table.playouts_MAST[move_code]

                policy[i] = math.exp(amaf_victory_rate / exploration_parameter)

            # On crée ensuite le vecteur qui servira de politique pour tirer le coup dans le playout
            return policy / policy.sum()

    def display(self, display_mode=None, figsize=(6,6), infos=True):
        """
        Fonction pour afficher le board.
        :param display_mode 'names' pour avoir les coordonnées des cases, 'content' pour les valeurs contenues
        :param infos : mettre True pour avoir les informations sur la partie
        """
        G = self.board
        pos = {}
        letters2position = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7, 'i': 8}

        node_colors = []

        fig = plt.figure(1, figsize=figsize)

        if infos is True:
            plt.title(f'Turn: {INT2STRING[self.turn]} - Hashcode: {self.hashcode}')
            plt.text(-1, -1, 'RED POOL: ' + str(self.piece_pools[RED][1]), color='red')
            plt.text(7, -1, 'BLUE POOL: ' + str(self.piece_pools[BLUE][1]), color='blue')
            if self.map.reference == "P32-D3-S48-v1":
                plt.text(3, -1, 'GREEN POOL: ' + str(self.piece_pools[GREEN][1]), color='green')

        plt.text(-1, 10, 't=' + str(self.game_time))

        for n, content in nx.get_node_attributes(G, 'content').items():
            pos[n] = (letters2position[n[0]], int(n[1]))

            # On regroupe par couleurs

            if content == EMPTY:
                node_colors.append('gray')
            elif content == RED:
                node_colors.append('red')
            elif content == BLUE:
                node_colors.append('blue')
            elif content == GREEN:
                node_colors.append('green')
            elif content == BLOCK:
                node_colors.append('black')
            elif content == GOAL:
                node_colors.append('purple')

        if display_mode is None:  # On affichera juste les couleurs
            nx.draw(G, pos, with_labels=False, node_color=node_colors)
        elif display_mode == 'content':  # Sinon on affiche les valeurs des noeuds.
            labels = nx.get_node_attributes(G, 'content')
            nx.draw(G, pos, labels=labels, node_color=node_colors)
        elif display_mode == 'names':  # Ou encore afficher les noms des cases.
            nx.draw(G, pos, with_labels=True, node_color=node_colors)

        plt.close()
        return fig

    def copy(self):
        cop = Board(mapp=self.map)

        cop.map = self.map

        for n, data in self.board.nodes(data=True):
            cop.change_content(n, new_content=data['content'])

        cop.hashcode = self.hashcode
        cop.hash_table = self.hash_table
        cop.hash_turn = self.hash_turn
        cop.transposition_table = self.transposition_table

        cop.game_time = self.game_time

        if self.map.reference == REF2:
            cop.piece_pools = {RED: ['a0', self.piece_pools[RED][1]],
                               BLUE: ['i0', self.piece_pools[BLUE][1]]}
        if self.map.reference == REF3:
            cop.piece_pools = {
                RED: ['a0', self.piece_pools[RED][1]],
                BLUE: ['i0', self.piece_pools[BLUE][1]],
                GREEN: ['e0', self.piece_pools[GREEN][1]]
            }

        cop.over = self.over
        cop.winner = copy.deepcopy(self.winner)
        cop.turn = self.turn
        return cop

    def update_MAST(self, winner, played_moves_codes: List[int]):
        treated_moves = set()
        for move_code in played_moves_codes:
            if move_code in treated_moves:
                continue
            self.transposition_table.playouts_MAST[move_code] += 1
            self.transposition_table.win_MAST[move_code][winner] += 1
            treated_moves.add(move_code)

    def update_AMAF(self, table_entry: List, winner, played_moves_codes: List[int]):
        treated_moves = set()
        for move_code in played_moves_codes:
            # On va devoir vérifier que le code a pas déjà été compté dans les statistiques
            if move_code in treated_moves:
                # Si c'est le cas, on passe au coup suivant directement
                continue
            # Sinon, on met à jour les statistiques AMAF de la table.
            table_entry[3][move_code] += 1  # Nb de fois que le coup a été joué
            table_entry[4][move_code][winner] += 1  # mise à jour du nb de victoires.
            treated_moves.add(move_code)

    def get_grouped_moves(self, move_list):
        grouped_moves = [[]]
        for m in move_list:
            if m.block is False:
                grouped_moves[0].append(m)  # La première liste sera celle qui contient les coups "normaux"

            # On va ensuite faire une liste par coup qui prend une barricade.
            else:
                found = False
                for group in grouped_moves[1:]:
                    if group[0].start_node == m.start_node and group[0].end_node == m.end_node:
                        group.append(m)
                        found = True
                if not found:
                    grouped_moves.append([m])
        return grouped_moves

    @staticmethod
    def get_situation_1(hash_table, hash_turn):
        b = Board(hash_table, hash_turn, mapp=Map("P32-D3-S48-v1"))
        b.change_content('e8', RED)
        b.piece_pools[RED][1] -= 1
        b.change_content('b8', BLOCK)
        b.change_content('c8', BLOCK)
        b.change_content('d8', BLOCK)
        b.change_content('f6', BLOCK)
        b.change_content('g6', BLOCK)

        b.change_content('b3', EMPTY)
        b.change_content('d3', EMPTY)
        b.change_content('f3', EMPTY)
        b.change_content('e5', EMPTY)

        b.change_content('b7', GREEN)
        b.piece_pools[GREEN][1] -= 1
        b.change_content('b6', BLUE)
        b.piece_pools[BLUE][1] -= 1

        b.turn = BLUE

        return b

    @staticmethod
    def get_situation_2(hash_table, hash_turn):
        b = Board(hash_table, hash_turn, mapp=Map("P32-D3-S48-v1"))
        b.change_content('e8', RED)
        b.piece_pools[RED][1] -= 1
        b.change_content('b8', BLOCK)
        b.change_content('c8', BLOCK)
        b.change_content('d8', BLOCK)
        b.change_content('f6', BLOCK)
        b.change_content('g6', BLOCK)
        b.change_content('c6', BLOCK)

        b.change_content('b3', EMPTY)
        b.change_content('d3', EMPTY)
        b.change_content('f3', EMPTY)
        b.change_content('e5', EMPTY)
        b.change_content('e0', EMPTY)

        b.change_content('b7', GREEN)
        b.change_content('d6', GREEN)
        b.piece_pools[GREEN][1] -= 2

        b.change_content('b6', BLUE)
        b.piece_pools[BLUE][1] -= 1

        b.turn = BLUE

        return b

    @staticmethod
    def get_situation_3(hash_table, hash_turn):
        b = Board(hash_table, hash_turn, mapp=Map("P32-D3-S48-v1"))
        b.change_content('c5', RED)
        b.change_content('d5', RED)
        b.piece_pools[RED][1] -= 2

        b.change_content('d8', BLOCK)
        b.change_content('h7', BLOCK)
        b.change_content('h8', BLOCK)
        b.change_content('h6', BLOCK)
        b.change_content('b7', BLOCK)
        b.change_content('g6', BLOCK)

        b.change_content('b3', EMPTY)
        b.change_content('h3', EMPTY)
        b.change_content('d3', EMPTY)
        b.change_content('f3', EMPTY)
        b.change_content('e5', EMPTY)
        b.change_content('e6', EMPTY)
        b.change_content('a0', EMPTY)

        b.change_content('d6', BLUE)
        b.piece_pools[BLUE][1] -= 1

        b.change_content('c6', GREEN)
        b.piece_pools[GREEN][1] -= 1

        b.turn = BLUE

        return b

    @staticmethod
    def get_situation_4(hash_table, hash_turn):
        b = Board(hash_table, hash_turn, mapp=Map("P32-D3-S48-v1"))
        b.change_content('b6', RED)
        b.change_content('b7', RED)
        b.piece_pools[RED][1] -= 2
        b.change_content('b8', BLOCK)
        b.change_content('c8', BLOCK)
        b.change_content('d8', BLOCK)
        b.change_content('h7', BLOCK)
        b.change_content('h8', BLOCK)
        b.change_content('h6', BLOCK)

        b.change_content('b3', EMPTY)
        b.change_content('d3', EMPTY)
        b.change_content('f3', EMPTY)
        b.change_content('e5', EMPTY)
        b.change_content('a0', EMPTY)
        b.change_content('i0', EMPTY)
        b.change_content('e8', EMPTY)

        b.change_content('c6', GREEN)
        b.piece_pools[GREEN][1] -= 1

        b.change_content('e6', BLUE)
        b.change_content('d6', BLUE)
        b.piece_pools[BLUE][1] -= 2

        b.turn = BLUE

        return b

    @staticmethod
    def get_situation_4bis(hash_table, hash_turn):
        b = Board(hash_table, hash_turn, mapp=Map("P32-D3-S48-v1"))
        b.change_content('c6', RED)
        b.change_content('b7', RED)
        b.piece_pools[RED][1] -= 2
        b.change_content('b8', BLOCK)
        b.change_content('c8', BLOCK)
        b.change_content('d8', BLOCK)
        b.change_content('h7', BLOCK)
        b.change_content('h8', BLOCK)
        b.change_content('h6', BLOCK)

        b.change_content('b3', EMPTY)
        b.change_content('d3', EMPTY)
        b.change_content('f3', EMPTY)
        b.change_content('e5', EMPTY)
        b.change_content('a0', EMPTY)
        b.change_content('i0', EMPTY)
        b.change_content('e8', EMPTY)

        b.change_content('b6', GREEN)
        b.piece_pools[GREEN][1] -= 1

        b.change_content('e6', BLUE)
        b.change_content('d6', BLUE)
        b.piece_pools[BLUE][1] -= 2

        b.turn = BLUE

        return b