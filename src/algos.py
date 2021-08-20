import math
import random

import numpy as np

from src.board import Board


BLOCK = 0
RED = 1
BLUE = 2
GREEN = 3
EMPTY = 4
GOAL = -1

MAX_DICE = 3
INT2STRING = {RED: 'RED', BLUE: 'BLUE', EMPTY: 'EMPTY', BLOCK: 'BLOCK'}


def flat(board: Board, dice_score: int, nb_playout: int):
    valid_moves = board.valid_moves(dice_score)

    best_score = 0

    if len(valid_moves) == 0:
        return None
    else:
        best_move = valid_moves[0]

    for move in valid_moves:  # Pour chaque move, on fait un certain nombre de playout
        # et on va faire des stats sur ces derniers
        print("Evalutation de", move, end=" ")
        sum_wins = 0

        for p in range(nb_playout):
            b = board.copy()
            b.play(move)
            played = []
            winner = b.playout_MAST(played, exploration_parameter=0.22)
            board.update_table(winner, played)

            if winner == move.player:
                sum_wins += 1

        score = sum_wins / nb_playout

        if score > best_score:
            print("le score a été battu", end=' ')
            best_score = score
            best_move = move
        print(f'[{score * nb_playout}/{nb_playout}]')
    print(f"Meilleur move : {best_move} [{best_score * nb_playout}/{nb_playout}]")
    return best_move


def UCB(board: Board, dice_score, nb_playouts):  # Ici nb_playouts est le nombre TOTAL de playouts qu'on va faire
    valid_moves = board.valid_moves(dice_score)  # On veut faire des statistiques sur chacun de ces coups

    # Il faut faire une extension des coups pour pouvoir faire des stats sur les coups qui bougent des blocs.

    sums = [0 for i in range(len(valid_moves))]
    nb_visits = [0 for i in range(len(valid_moves))]

    for p in range(nb_playouts):
        best_score = -1
        best_moves = []

        # On cherche d'abord le coup qui maximise la formule UCB
        for m in range(len(valid_moves)):

            if nb_visits[m] == 0:
                score = 10000000  # Pour visiter les coups non visités en priorité, on fait comme s'ils avaient un score très élevé

            if nb_visits[m] > 0:
                # Formule UCB :
                score = sums[m] / nb_visits[m] + 0.5 * math.sqrt(math.log(p) / nb_visits[m])
                # print('score UCB : ', score)

            if score > best_score:
                best_score = score
                best_moves = [m]
            if score == best_score: # On construit une liste de tous les meilleurs coups
                best_moves.append(m)


        # Maintenant il faut jouer un des meilleurs coups

        chosen_move = random.choice(best_moves)

        b = board.copy()
        b.play(valid_moves[chosen_move])

        # Puis faire un playout et récupérer le résultat
        played = []
        winner = b.playout_MAST(played, exploration_parameter=0.23)
        board.update_table(winner, played)  # On met à jour la table pour les prochains playouts

        # Et save les stats
        if winner == board.turn:
            sums[chosen_move] += 1
        nb_visits[chosen_move] += 1

    print(nb_visits)
    print(sums)
    print('coup choisi : ', np.argmax(nb_visits), valid_moves[np.argmax(nb_visits)])

    # Une fois qu'on a terminé tous les playouts, il faut retourner le meilleur coup :
    # Selon la formule UCB, le coup qui minimise le regret est le coup qui a été le plus joué

    return valid_moves[np.argmax(nb_visits)]


# Algorithme UCT
def UCT(board: Board, dice_score, played, mode=1, c=0.4):
    if board.over:  # Si l'état est terminal on renvoie le score.
        return board.winner

    # sinon on récupère l'entrée dans la table de transposition.
    t = board.look_table()

    if t != None:  # Si différent de None alors l'entrée est déjà présente. On va faire UCB dessus
        best_score = -1
        # print(f"Etat déja vu {t[0]} fois")
        # On récupère la liste des coups légaux
        moves = board.valid_moves(dice_score)

        if len(moves) == 0:
            board.play(None)
            res = UCT(board, random.randint(1, board.map.max_dice), played, mode, c)
            t[0] += 1  # On a bien vu l'etat mais on a joué aucun coup
            return res

        else:
            player = moves[0].player
            best_moves = []
            # On va choisir le move qui maximise UCB, sauf s'il y a des coups non essayés.
            for m in range(len(moves)):
                score = 1000000.0

                if t[1][m] > 0:  # Si le nombre de fois que le coup a été joué est supérieur à 0
                    Q = t[2][m][player] / t[1][m]  # Calcul du nombre de victoires moyenne du joueur actuel

                    score = Q + c * math.sqrt(math.log(t[0]) / t[1][m])  # Formule UCB

                if score > best_score:
                    best_score = score
                    best_moves = [m]
                elif score == best_score:
                    best_moves.append(m)

            # On joue un des meilleurs coups selon UCB
            choice = random.choice(best_moves)
            board.play(moves[choice])
            played.append(moves[choice])

            # Puis on fait un appel récursif pour le nouveau board avec un lancer de dé aléatoire

            winner = UCT(board, random.randint(1, board.map.max_dice), played, mode, c)  # On obtiendra un résultat sur ce board

            # On l'utilise pour mettre à jour les statistiques du meilleur coup.

            t[0] += 1  # Nb de fois qu'on a vu l'état
            t[1][choice] += 1  # Nb de playouts qui commencent par ce coup
            t[2][choice][winner] += 1  # Nb de victoires de RED pour ce coup
            # Et on le remonte aux étapes récursives précédentes.
            return winner

    else:  # Si l'etat n'a jamais été visité, on ajoute juste l'état dans la table et on retourne le résultat d'un
        # playout
        board.new_table_entry()
        res = board.playout_MAST(played, exploration_parameter=0.5, mode=mode)
        return res


# La fonction prend en paramètre un état et un nombre de simulations et qui va renvoyer
# le meilleur coup calculé grâce à UCT


def best_move_UCT(board: Board, dice_score, nb_playouts, mode=1, c=0.4):

    board.transposition_table.table = {}
    for i in range(nb_playouts):  # On fait n simulations
        b1 = board.copy()
        played = []
        winner = UCT(b1, dice_score, played, mode, c)  # On obtient un résultat.
        board.update_table(winner, played)

    # Donc là on a fait n playout en ajoutant à chaque fois un état dans l'abre c'est à dire dans la table
    # de transposition.

    # Il faut maintenant récupérer le coup le plus simulé

    t = board.look_table()  # On récup la racine de l'arbre dans la table

    # Les coups sont toujours retournés dans le même ordre pour un état de plateau donné.
    moves = board.valid_moves(dice_score)

    # Et on va prendre le coup le plus simulé c'est à dire celui qui a le nombre de playouts
    # le plus grand !

    best_moves = []
    best_value = 0

    for m in range(len(moves)):
        print('Pour', moves[m], ':', t[1][m], 'playout')
        if t[1][m] > best_value:
            best_value = t[1][m]
            best_moves = [m]

        if t[1][m] == best_value:
            best_moves.append(m)
    print("La table contient :", len(board.transposition_table.table))
    return moves[random.choice(best_moves)]
