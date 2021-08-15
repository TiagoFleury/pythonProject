import copy
import math

import numpy as np

from src.map import Map
from src.move import Move
from src.utils import timeit, figs2gif
from src.table import Table
import networkx as nx
import random
import matplotlib.pyplot as plt
from typing import Union

BLOCK = 0
RED = 1
BLUE = 2
EMPTY = 3
GOAL = -1

SWITCH = {RED: BLUE, BLUE: RED}
INT2STRING = {RED: 'RED', BLUE: 'BLUE'}

MAX_DICE = 3


class Board:

    def __init__(self, hash_table=None, hash_turn=None, mapp=Map("P22-D3-S34-v1")):

        self.hashcode = 0  # On aura un hashcode unique pour chaque position de jeu possible (voir section hachage de Zobrist)

        self.piece_pools = {RED: ['a0', 2], BLUE: ['i0', 2]}

        self.turn = RED

        self.game_time = 0

        self.over = False

        self.score = None  # Sera à 1 si RED gagne, 0 si BLUE gagne.

        self.hash_table = hash_table
        self.hash_turn = hash_turn

        self.transposition_table = Table(mapp)

        self.map = mapp
        self.board = mapp.get_board()

    def get_content(self, node_name):
        return self.board.nodes[node_name]['content']

    def change_content(self, node_name, new_content):
        if new_content not in [RED, BLUE, BLOCK, GOAL, EMPTY]:
            print("Mauvaise valeur pour 'content' !, vous avez placé : ", new_content)
        else:
            self.board.nodes[node_name]['content'] = new_content

    def look_table(self):
        return self.transposition_table.look(self)

    def new_table_entry(self):
        self.transposition_table.add(self)

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
                        # Une fois que le move est validé, il faut spécifier ou envoyer le block si c'est nécessaire

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

            opponent_color = SWITCH[move.player]

            if move.content_end_node == GOAL:
                self.over = True
                if self.turn == RED:
                    self.score = 1
                else:
                    self.score = 0

            if move.content_end_node == opponent_color:
                opponent_pool_node = self.piece_pools[opponent_color][0]
                # On enlève la pièce
                self.change_content(move.end_node, EMPTY)  # Ligne possiblement inutile
                # On actualise le hash_code
                self.hashcode = self.hashcode ^ self.hash_table[move.end_node][opponent_color]

                # Puis on replace la pièce dans son pool
                self.piece_pools[opponent_color][1] += 1  # On incrémente le nombre de pièces présentes dans le pool
                # On actualise le hashcode en utilisant cette valeur

                self.hashcode = self.hashcode ^ self.hash_table[opponent_pool_node][self.piece_pools[opponent_color][1]]

                self.change_content(opponent_pool_node, opponent_color)  # On met une pièce sur la case.

            if move.block:  # Si c'est un coup qui déplace un block.

                # On enlève le BLOCK
                self.change_content(move.end_node, EMPTY)  # Ligne possiblement inutile également
                self.hashcode = self.hashcode ^ self.hash_table[move.end_node][BLOCK]

                # Ensuite il faut replacer le block quelque part

                self.change_content(move.chosen_placement, BLOCK)
                self.hashcode = self.hashcode ^ self.hash_table[move.chosen_placement][BLOCK]

            # Enfin, il faut placer la pièce du joueur et actualiser une dernière fois le hashcode

            self.change_content(move.end_node, move.player)
            self.hashcode = self.hashcode ^ self.hash_table[move.end_node][move.player]

        # On termine le tour en changeant de tour et en appliquant le hashcode correspondant
        self.turn = SWITCH[self.turn]
        self.hashcode = self.hashcode ^ self.hash_turn

        self.game_time += 1

        return 0

    def playout(self):  #
        """Fonction qui joue aléatoirement une partie à partir de l'état actuel et qui retourne le résultat."""

        while not self.over:
            valid_moves = self.valid_moves(random.randint(1, MAX_DICE))  # Récupération des moves valides
            if len(valid_moves) != 0:
                chosen_move = random.choice(valid_moves)
                self.play(chosen_move)
            else:
                # Dans ce cas, il n'y a pas de coup jouable
                self.play(None)  # On passe son tour.

        return self.score  # On va retourner 0 si c'est RED qui gagne et 1 si c'est BLUE

    def playout_AMAF(self):
        """Fonction qui joue un playout tout en sauvegardant les statistiques AMAF pour tous les coups joués """
        played = []
        while not self.over:
            dice_score = random.randint(1, self.map.max_dice)
            valid_moves = self.valid_moves(dice_score)
            if len(valid_moves) != 0:
                chosen_move = random.choice(valid_moves)
                chosen_destination = None


    def playout_with_policy(self, played_moves=None, exploration_parameter=1, save_gif=False):

        if played_moves is None:
            played_moves = []

        figs = []
        if save_gif is True:
            figs = [self.display('names')]

        while not self.over: # and self.game_time < 4:

            dice_score = random.randint(1, self.map.max_dice)
            valid_moves = self.valid_moves(dice_score)


            if len(valid_moves) != 0:
                policy = self.get_policy(valid_moves, exploration_parameter=exploration_parameter)
                # print("Policy :", policy,"sum:",policy.sum())
                chosen_move = random.choices(valid_moves, policy)[0]
                played_moves.append(chosen_move)
                self.play(chosen_move)

            else:
                self.play(None)

            if save_gif is True:
                figs.append(self.display('names'))

        if save_gif is True:
            figs2gif(figs, "new_playout_gt"+str(self.game_time)+".gif")

        return self.score

    def get_policy(self, move_list, exploration_parameter=1):
        policy = np.zeros(len(move_list))

        for i, move in enumerate(move_list):
            move_code = move.code(self.map)
            # On commence par faire la somme des exp des taux de victoire AMAF
            # et préparer la politique de tirage des coups
            if self.transposition_table.playouts_amaf[move_code] == 0:
                amaf_victory_rate = 0
            else:
                amaf_victory_rate = self.transposition_table.win_amaf[move_code] / \
                                    self.transposition_table.playouts_amaf[move_code]
                if move.player == BLUE:
                    amaf_victory_rate = 1 - amaf_victory_rate

            policy[i] = math.exp(amaf_victory_rate / exploration_parameter)


        # On crée ensuite le vecteur qui servira de politique pour tirer le coup dans le playout
        return policy / policy.sum()

    def display(self, display_mode=None, figsize=(6, 6), infos=True):
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
            plt.text(-1, 8, 'RED POOL: ' + str(self.piece_pools[RED][1]), color='red')
            plt.text(7, 8, 'BLUE POOL: ' + str(self.piece_pools[BLUE][1]), color='blue')

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
        cop = Board()
        cop.board = nx.Graph()
        for n, data in self.board.nodes(data=True):
            cop.board.add_node(n, content=data['content'])
        cop.board.add_edges_from(self.board.edges)

        cop.hashcode = self.hashcode
        cop.hash_table = self.hash_table
        cop.hash_turn = self.hash_turn
        cop.game_time = self.game_time
        cop.piece_pools = {RED: ['a0', self.piece_pools[RED][1]], BLUE: ['i0', self.piece_pools[BLUE][1]]}

        cop.over = self.over
        cop.score = self.score
        cop.turn = self.turn
        cop.transposition_table = self.transposition_table
        return cop

    def update_table(self, score, played_moves: list[tuple[Move, str]]):
        for move in played_moves:
            move_code = move.code(self.map)
            self.transposition_table.playouts_amaf[move_code] += 1
            self.transposition_table.win_amaf[move_code] += score


