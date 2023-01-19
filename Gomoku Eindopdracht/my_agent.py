import random
import gomoku
import time
import numpy as np
from gomoku import Board, Move, GameState


class my_player:
    """This class specifies a player that just does random moves.
    The use of this class is two-fold: 1) You can use it as a base random roll-out policy.
    2) it specifies the required methods that will be used by the competition to run
    your player
    """

    def __init__(self, black_: bool = True):
        """Constructor for the player."""
        self.black = black_

    def new_game(self, black_: bool):
        """At the start of each new game you will be notified by the competition.
        this method has a boolean parameter that informs your agent whether you
        will play black or white.
        """
        self.black = black_

    def rollout(self, leaf) -> float:
        #TODO implement this function
        return 0.0

    def backup_value(self, leaf, val):
        #TODO implement this function
        print('')

    def move(
        self, state: GameState, last_move: Move, max_time_to_move: int = 1000
    ) -> Move:
        """This is the most important method: the agent will get:
        1) the current state of the game
        2) the last move by the opponent
        3) the available moves you can play (this is a special service we provide ;-) )
        4) the maximum time until the agent is required to make a move in milliseconds [diverging from this will lead to disqualification].
        """
        #TODO add MCTS

        max_time = time.time() + max_time_to_move
        cur_time = time.time()

        cur_best_value = - np.inf

        #this outside of while-loop because only needed to be done once
        moves = gomoku.valid_moves(state)

        #choose random move as base (if out of time, at least a move)
        cur_move = random.choice(moves)

        while cur_time < max_time:
            n_leaf = random.choice(moves)

            val = self.rollout(n_leaf)
            self.backup_value(n_leaf, val)

            if val > cur_best_value:
              cur_best_value = val
              cur_move = n_leaf

            moves.remove(n_leaf)

            cur_time = time.time()

        return cur_move

    def id(self) -> str:
        """Please return a string here that uniquely identifies your submission e.g., "name (student_id)" """
        return "Emma Raijmakers (1784436)"
