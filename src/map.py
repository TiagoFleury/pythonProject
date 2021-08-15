import networkx as nx

BLOCK = 0
RED = 1
BLUE = 2
EMPTY = 3
GOAL = -1


class Map:

    def __init__(self, reference="P22-D3-S34-v1"):

        if reference == "P22-D3-S34-v1":

            self.reference = reference
            self.nb_players = 2
            self.nb_pieces = 2
            self.max_dice = 3
            self.possible_start_nodes = ['a0', 'i0', 'a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1', 'i1', 'b2', 'd2',
                                         'f2', 'h2', 'b3', 'c3', 'd3', 'e3', 'f3', 'g3', 'h3', 'c4', 'e4', 'g4', 'c5',
                                         'd5', 'e5', 'f5', 'g5', 'e6', 'e7', 'e8']

            self.possible_end_nodes = ['a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1', 'i1', 'b2', 'd2', 'f2', 'h2'
                , 'b3', 'c3', 'd3', 'e3', 'f3', 'g3', 'h3', 'c4', 'e4', 'g4', 'c5', 'd5', 'e5', 'f5', 'g5', 'e6'
                , 'e7', 'e8', 'e9']

            self.possible_block_placements = ['b2', 'd2', 'f2', 'h2', 'b3', 'c3', 'd3', 'e3', 'f3', 'g3', 'h3', 'c4',
                                              'e4', 'g4', 'c5', 'd5', 'e5', 'f5', 'g5', 'e6', 'e7', 'e8']

            self.content2code = {EMPTY: 0, RED: 1, BLUE: 1, GOAL: 2}
            self.player2code = {RED: 0, BLUE: 1}


        else:
            print('Erreur : Reference de la map inconnue')

        # C'est le nombre total de coup possible sans prendre en compte l'etat du plateau
        self.nb_possible_moves = (self.nb_players * len(self.possible_start_nodes) * len(self.possible_end_nodes) * (
                    self.nb_players - 1 + 2)) + (
                                         self.nb_players * len(self.possible_start_nodes) * len(
                                     self.possible_end_nodes) * len(self.possible_block_placements))

    def get_board(self):
        if self.reference == "P22-D3-S34-v1":
            g = nx.Graph()

            # Ajout des nodes
            g.add_node("a0", content=RED)
            g.add_node("i0", content=BLUE)

            g.add_node("a1", content=EMPTY)
            g.add_node("b1", content=EMPTY)
            g.add_node("c1", content=EMPTY)
            g.add_node("d1", content=EMPTY)
            g.add_node("e1", content=EMPTY)
            g.add_node("f1", content=EMPTY)
            g.add_node("g1", content=EMPTY)
            g.add_node("h1", content=EMPTY)
            g.add_node("i1", content=EMPTY)

            g.add_node("b2", content=EMPTY)
            g.add_node("d2", content=EMPTY)
            g.add_node("f2", content=EMPTY)
            g.add_node("h2", content=EMPTY)

            g.add_node("b3", content=BLOCK)
            g.add_node("c3", content=EMPTY)
            g.add_node("d3", content=BLOCK)
            g.add_node("e3", content=EMPTY)
            g.add_node("f3", content=BLOCK)
            g.add_node("g3", content=EMPTY)
            g.add_node("h3", content=BLOCK)

            g.add_node("c4", content=EMPTY)
            g.add_node("e4", content=EMPTY)
            g.add_node("g4", content=EMPTY)

            g.add_node("c5", content=EMPTY)
            g.add_node("d5", content=EMPTY)
            g.add_node("e5", content=BLOCK)
            g.add_node("f5", content=EMPTY)
            g.add_node("g5", content=EMPTY)

            g.add_node("e6", content=EMPTY)
            g.add_node("e7", content=EMPTY)
            g.add_node("e8", content=EMPTY)
            g.add_node("e9", content=GOAL)

            # Ajout des edges
            g.add_edges_from([("a0", "a1"), ("i0", "i1"),
                              ("a1", "b1"), ("b1", "c1"), ("c1", "d1"), ("d1", "e1"), ("e1", "f1"), ("f1", "g1"),
                              ("g1", "h1"), ("h1", "i1"),
                              ("b1", "b2"), ("b2", "b3"), ("d1", "d2"), ("d2", "d3"), ("f1", "f2"), ("f2", "f3"),
                              ("h1", "h2"), ("h2", "h3"),
                              ("b3", "c3"), ("c3", "d3"), ("d3", "e3"), ("e3", "f3"), ("f3", "g3"), ("g3", "h3"),
                              ("c3", "c4"), ("c4", "c5"), ("e3", "e4"), ("e4", "e5"), ("g3", "g4"), ("g4", "g5"),
                              ("c5", "d5"), ("d5", "e5"), ("e5", "f5"), ("f5", "g5"),
                              ("e5", "e6"), ("e6", "e7"), ("e7", "e8"), ("e8", "e9")
                              ])

            return g
        else:
            print("Erreur : Mauvaise référence pour la map")
            return None
