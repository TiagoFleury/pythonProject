# Ce sera la structure qui va stocker les stats pour les versions de MonteCarlo qui contrôlent la descente de l'arbre.

from src.map import Map


class Table:
    def __init__(self, mapp: Map = Map(reference="P22-D3-S34-v1")):
        '''
        On a besoin de pouvoir stocker pour chaque état :
            - Le nombre de playouts qui ont été faits dans cet état
            Pour chaque coup possible DANS CET ETAT :
                - Le nombre de victoires
                - Le nombre de fois que le coup a été joué
        '''

        # On aura besoin de listes de la taille du nombre maximum de coups possibles.

        max_different_paths = 9

        self.max_moves_for_a_state = max_different_paths * mapp.nb_players * mapp.nb_pieces * len(mapp.possible_block_placements)

        self.table = {}

        self.win_amaf = [0 for i in range(mapp.nb_possible_moves)]
        self.playouts_amaf = [0 for i in range(mapp.nb_possible_moves)]

    def add(self, board):
        nplayouts = [0.0 for i in range(self.max_moves_for_a_state)]
        nwins = [0.0 for i in range(self.max_moves_for_a_state)]

        self.table[board.hashcode] = [0, nplayouts, nwins]

    def look(self, board):  # Retourne None, si l'état n'est pas présent dans la table.
        return self.table.get(board.hashcode, None)


if __name__ == '__main__':
    print('bonjour')
    t = Table()
    print(t.max_moves_for_a_state)
