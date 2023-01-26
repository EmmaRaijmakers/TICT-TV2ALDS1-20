import random
import gomoku
import time
import numpy as np
from gomoku import Board, Move, GameState
import GmUtils


class my_player:
    """This class specifies a player that just does random moves.
    The use of this class is two-fold: 1) You can use it as a base random roll-out policy.
    2) it specifies the required methods that will be used by the competition to run
    your player
    """
    #TODO tree en child vars? etc
    tree = {}

    def __init__(self, black_: bool = True):
        """Constructor for the player."""
        self.black = black_

    def new_game(self, black_: bool):
        """At the start of each new game you will be notified by the competition.
        this method has a boolean parameter that informs your agent whether you
        will play black or white.
        """
        self.black = black_

    #This function has a time complexity of
    def find_spot_to_expand(self, moves):
        return random.choice(moves)

    #This function has a time complexity of O(n) because it places moves until (worst case) the board is filled 
    def rollout(self, leaf, moves) -> float:
        #TODO Test this function

        #TODO voeg dit toe \/
        """NumPy copy:

        >>> pybench "cp_np = np.copy(ref_np)"
        100000 loops, best of 3: 6.03 usec per loop
        Copying to pre-created NumPy array:

        >>> pybench "np.copyto(cp_np, ref_np)"
        100000 loops, best of 3: 4.52 usec per loop"""

        current_moves = moves.copy()
        current_board = Board.deepcopy()

        #TODO wat do als er geen valid moves meer zijn?
        # if len(current_moves) == 0:
        #     return 0.0

        end_state = False

        #current player to make a move
        current_player_mine = True

        #to make sure the first move is the par
        first_run = True

        while not end_state:
            if first_run:
                action = leaf
                first_run = False
            else:
                action = random.choice(current_moves)
            current_moves.remove(action)

            #play a move based on who is to move and what color they have
            if current_player_mine and self.black:
                GmUtils.addMoveToBoard(current_board, action, 1) 
            elif current_player_mine and not self.black:
                GmUtils.addMoveToBoard(current_board, action, 2) 
            elif not current_player_mine and self.black:
                GmUtils.addMoveToBoard(current_board, action, 2)
            elif not current_player_mine and not self.black:
                GmUtils.addMoveToBoard(current_board, action, 1)  

            #check if the game is won
            win = GmUtils.isWinningMove(action, current_board)

            #if win return the right value based on which player won (or neither)
            if win and current_player_mine:
                return 1
            elif win and not current_player_mine:
                return 0
            elif len(current_moves) == 0:
                return 0.5

            end_state = win
        
        #niet nodig ??
        return 0.5

    #This function has a time complexity of
    def backup_value(self, leaf, val):
        #TODO implement this function
        print('')

    #This function has a time complexity of
    def move(
        self, state: GameState, last_move: Move, max_time_to_move: int = 1000
    ) -> Move:
        """This is the most important method: the agent will get:
        1) the current state of the game
        2) the last move by the opponent
        3) the available moves you can play (this is a special service we provide ;-) )
        4) the maximum time until the agent is required to make a move in milliseconds [diverging from this will lead to disqualification].
        """
        #TODO add MCTS + test this function

        max_time = time.time() + max_time_to_move
        cur_time = time.time()

        cur_best_value = - np.inf

        #this outside of while-loop because only needed to be done once
        moves = gomoku.valid_moves(state)

        #choose random move as base (if out of time, at least a move)
        cur_move = random.choice(moves)

        while cur_time < max_time:
            # n_leaf = random.choice(moves)

            n_leaf = self.find_spot_to_expand(moves)

            # val = self.rollout(n_leaf)
            val = self.rollout(n_leaf, moves)
            self.backup_value(n_leaf, val)

            if val > cur_best_value:
              cur_best_value = val
              cur_move = n_leaf

            moves.remove(n_leaf)

            cur_time = time.time()

        return cur_move

    #This function has a time complexity of O(1) because it instantly returns a value
    def id(self) -> str:
        """Please return a string here that uniquely identifies your submission e.g., "name (student_id)" """
        return "Emma Raijmakers (1784436)"
