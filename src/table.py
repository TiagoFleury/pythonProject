# Ce sera la structure qui va stocker les stats pour les versions de MonteCarlo qui contrôlent la descente de l'arbre.

from src.map import Map

RED = 1
BLUE = 2
GREEN = 3

class Table:
    def __init__(self, mapp: Map):
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
        if mapp.reference == "P22-D3-S34-v1":
            self.win_MAST = [{RED: 0, BLUE: 0} for i in range(mapp.nb_possible_moves)]
        elif mapp.reference == "P32-D3-S48-v1":
            self.win_MAST = [{RED: 0, BLUE: 0, GREEN: 0} for i in range(mapp.nb_possible_moves)]

        self.playouts_MAST = [0 for i in range(mapp.nb_possible_moves)]

    def add(self, board, amaf: bool):
        nplayouts = [0.0 for i in range(self.max_moves_for_a_state)]
        nwins_amaf = None
        nplayouts_amaf = None

        if board.map.reference == "P22-D3-S34-v1":
            nwins = [{RED: 0, BLUE: 0} for i in range(self.max_moves_for_a_state)]
            if amaf is True: # Si on utilise l'algorithme RAVE ou GRAVE, il faut stocker également les statistiques AMAF
                nwins_amaf = [{RED: 0, BLUE: 0} for i in range(board.map.nb_possible_moves)]
                nplayouts_amaf = [0 for i in range(board.map.nb_possible_moves)]

        elif board.map.reference == "P32-D3-S48-v1":
            nwins = [{RED: 0, BLUE: 0, GREEN: 0} for i in range(self.max_moves_for_a_state)]
            if amaf is True:
                nwins_amaf = [{RED: 0, BLUE: 0, GREEN: 0} for i in range(board.map.nb_possible_moves)]
                nplayouts_amaf = [0 for i in range(board.map.nb_possible_moves)]
        else:
            print("Pas de référence de map connue dans Table.add()")
            nwins = None

        if amaf is True:
            self.table[board.hashcode] = [0, nplayouts, nwins, nplayouts_amaf, nwins_amaf]
        else:
            self.table[board.hashcode] = [0, nplayouts, nwins]

    def look(self, board):  # Retourne None, si l'état n'est pas présent dans la table.
        return self.table.get(board.hashcode, None)



