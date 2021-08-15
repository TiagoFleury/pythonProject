import copy
from typing import List, Union, Tuple, Any

BLOCK = 0
RED = 1
BLUE = 2
EMPTY = 3
GOAL = -1

SWITCH = {RED: BLUE, BLUE: RED}
INT2STRING = {RED: 'RED', BLUE: 'BLUE'}


class Move:

    def __init__(self, player, start_node, end_node, content_end_node, path, dice_score):
        self.player = player
        self.start_node = start_node
        self.end_node = end_node
        self.content_end_node = content_end_node
        self.path = path
        self.dice_score = dice_score

        self.block = None  # Sera à True si le coup déplace un block et à false sinon.
        self.block_placements = []

        self.chosen_placement = None

    def is_valid(self, board):  # Checke si le coup est valide pour un certain plateau.
        # On aura déjà vérifié que les start_node et end_node sont bien reliés d'un chemin de taille dice_score
        # De plus, on part du principe que les chemins entre deux noeuds de taille <= MAX_DICE sont uniques !
        # Donc si un chemin contient un BLOCK, on peut directement invalider le move.

        # Il suffit donc de vérifier :
        # 1. Que la case d'arrivée n'est pas de la couleur self.player

        if self.content_end_node == self.player or self.end_node[1] == '0':  # On a pas le droit de retourner dans les pools
            return False

        # 2. Que le chemin n'est pas bloqué par un BLOCK.
        for node in self.path[:-1]:
            if board.get_content(node) == BLOCK:
                return False

        # A partir de là le Move est déjà valide.
        # Cependant, dans le cas où on tombe sur un block, il faut choisir où le poser. Les options possibles sont toutes les cases où il n'y a pas de pièce sauf les 2 premières lignes

        if self.content_end_node == BLOCK:
            self.block = True
            # On va sauvegarder dans l'attribut block_placements toutes les positions possibles pour le block
            self.block_placements = [node for node, data in board.board.nodes(data=True) if
                                     data['content'] == EMPTY and node[1] != '0' and node[1] != '1']

            # Il faut également ajouter la case du pion initial car il aura bougé (seulement s'il est sur la troisième ligne ou plus)

            if self.start_node[1] != '0' and self.start_node[1] != '1':
                self.block_placements += [self.start_node]
        else:
            self.block = False

        return True

    @staticmethod
    def extend(move_list: list['Move']) -> list[tuple['Move', Union[str, None]]]:
        extended_list = []
        for move in move_list:
            if not move.block:
                extended_list.append((move, None))
            else:
                for pos in move.block_placements:
                    extended_list.append((move, pos))
        return extended_list

    def code(self, mapp):
        # Il faut associer à chaque coup possible un code pour pouvoir stocker les statistiques AMAF

        code = 0

        nb_options = mapp.nb_players - 1 + 2 # Sur la case d'arrivée, on peut arriver sur : ADVERSAIRE1, ADVERSAIRE2... ou EMPTY ou GOAL. On traite le cas des BLOCK à côté

        if self.content_end_node == BLOCK:
            code += mapp.possible_block_placements.index(self.chosen_placement) + nb_options  # +3 parce qu'il faut la place pour EMPTY, PLAYERS, GOAL
        else:
            code += mapp.content2code[self.content_end_node]

        code += mapp.possible_end_nodes.index(self.end_node) * (len(mapp.possible_block_placements) + nb_options)

        code += mapp.possible_start_nodes.index(self.start_node) * len(mapp.possible_end_nodes) * (len(mapp.possible_block_placements) + nb_options)

        code += mapp.player2code[self.player] * len(mapp.possible_start_nodes) * len(mapp.possible_end_nodes) * (len(mapp.possible_block_placements) + nb_options)

        return code

    def copy(self):
        m = Move(self.player,
                 self.start_node,
                 self.end_node,
                 self.content_end_node,
                 copy.deepcopy(self.path),
                 self.dice_score
                 )
        m.block = self.block
        m.block_placements = copy.deepcopy(self.block_placements)
        m.chosen_placement = self.chosen_placement
        return m

    def __str__(self):
        if self.block == True:
            if self.chosen_placement == None:
                return INT2STRING[self.player] + " move : " + str(
                    self.dice_score) + "(" + self.start_node + "," + self.end_node + ") - Block move - placements : " + str(
                    self.block_placements)
            else:
                return INT2STRING[self.player] + " move : " + str(
                    self.dice_score) + "(" + self.start_node + "," + self.end_node + ") B -> " + self.chosen_placement
        else:
            return INT2STRING[self.player] + " move : " + str(
                self.dice_score) + "(" + self.start_node + "," + self.end_node + ")"
