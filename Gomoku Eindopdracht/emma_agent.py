from __future__ import annotations # Needed for type hinting (Node as member in Node)
import random
import numpy as np
import gomoku
from gomoku import Move, GameState, Board, move
import copy
import time
from typing import Tuple
from GmUtils import GmUtils
from GmQuickTests import GmQuickTests

#TODO black = x = 1
#TODO white = o = 2

#TODO dingen gedaan om te verbeteren: tree opslaan, finished nodes toegevoegd?

class Node:
    def __init__(self, current_gamestate_: GameState, black_: bool, last_move_: Move = None, parent_: Node = None):
        self.current_gamestate = current_gamestate_
        self.last_move = last_move_

        self.parent = parent_
        self.children = []

        # Number of wins in children
        self.Q = 0

        # Number of visits to current node
        self.N = 0

        # Check if this node is fully expended (win, lose or draw)
        self.fully_expended = False

        self.black = black_

    # def add_child(self, move: Move, game_state_after_move: GameState) -> Node:
    #
    #     # Add given move to a copy of the board
    #     new_board = copy.deepcopy(self.current_gamestate[0])
    #     GmUtils.addMoveToBoard(new_board, move, 2 if self.black else 1)
    #
    #     # Add new child to current node
    #     new_gamestate = (new_board, self.current_gamestate[1] + 1)
    #     self.children.append(Node(new_gamestate, not self.black, game_state_after_move))
    #
    #     self.children.append(Node(game_state_after_move, not self.black, ))
    #
    #     is_valid, has_won, new_gamestate = gomoku.Move(self.current_gamestate, move)
    #
    #
    #     #
    #     # if is_valid:
    #     #     # do things
    #     #
    #     #     if has_won:
    #     #         # finished so,
    #
    #
    #     return Node(self.current_gamestate, move, self.parent)
    #
    #
    # # move up win in tree
    # def expend_down_once(self, move: Move):
    #     print("hi")
    #
    #     # move input

# This default base player does a random move
class EmmaPlayer:
    """This class specifies a player that just does random moves.
    The use of this class is two-fold: 1) You can use it as a base random roll-out policy.
    2) it specifies the required methods that will be used by the competition to run
    your player
    """
    #TODO var toevoegen om te checken of een child al volledig ondekt is (finished) zodat niet dubbel werk gedaan wordt

    def __init__(self, black_: bool = True):
        """Constructor for the player."""
        self.black = black_

        self.base_node = None

        #self.current_state = None
        #self.current_last_move = None

    def new_game(self, black_: bool):
        """At the start of each new game you will be notified by the competition.
        this method has a boolean parameter that informs your agent whether you
        will play black or white.
        """
        self.black = black_

    def move(self, state: GameState, last_move: Move, max_time_to_move: int = 1000) -> Move:
        print("move")
        """This is the most important method: the agent will get:
        1) the current state of the game
        2) the last move by the opponent
        3) the available moves you can play (this is a special service we provide ;-) )
        4) the maximum time until the agent is required to make a move in milliseconds [diverging from this will lead to disqualification].
        """
        #self.current_state = state
        #self.current_last_move = last_move

        #moves = GmUtils.getValidMoves(state[0], state[1])
        moves = gomoku.valid_moves(state)

        # create base node
        if self.base_node is None:
            self.base_node = Node(state, self.black, last_move)

        # expand tree in max time
        safe_time = 100  # TODO voor onderzoek experiment met dit
        max_time = time.time() + (max_time_to_move / 1000) - (safe_time / 1000)

        while time.time() < max_time:
            copy_board = copy.deepcopy(state[0])
            copy_gamestate = copy_board, state[1]
            copy_moves = copy.deepcopy(moves)
            self.find_spot_to_extend(copy_gamestate, copy_moves, self.base_node)

        best_move, best_child = self.calculate_best_move(self.base_node)
        self.base_node = best_child
        return best_move

    def find_spot_to_extend(self, state: GameState, moves: [Move], current_node: Node) -> None:
        print("expand_base_node")

        new_move = random.choice(moves) #TODO hier niet random maar een slimmere techniek vinden


        children_moves = []

        for child in self.base_node.children:
            children_moves.append(child.last_move)
        print(f'{children_moves} children movesfjdskfjdskfjdsfkjsd')


        #TODO wat als in een finished node komt? of als de tree volledig extended is?
        if (new_move not in children_moves) and (len(moves) > 0):
            new_node = Node(state, self.black, new_move, current_node)
            moves.remove(new_move)
            self.roll_down(new_node, moves)
        elif len(moves) > 0:
            new_base_node = self.base_node.children[children_moves.index(new_move)] #move and child index are the same
            moves.remove(new_move)
            self.find_spot_to_extend(new_base_node.current_gamestate, moves, new_base_node)

        # Function to roll down one node to the bottom
        #self.roll_down(new_gamestate, moves) #TODO choose node to extend

    #def roll_out

    def roll_down(self, node_to_roll_down:Node, moves: [Move]) -> None:
        print("roll_down")
        # do move, get if valid, has won and new gamestate

        # if won return and update node q and n

        # else get next list of valid moves (remove moves of children)
        # choice random move from this list
        # recursive into this function with next move and gamestate until base case has been reached.

        # node child met move x, check result, new child of child met random move y, check result ....

        is_winning = False
        #current_state = state
        current_moves = copy.copy(moves) #TODO copy nodig hier??
        current_node = node_to_roll_down

        while (not is_winning) and len(current_moves) > 0:
            # Choose a random move from the current valid moves and play that move
            new_move = random.choice(current_moves)

            is_valid, is_winning, new_state = gomoku.move(current_node.current_gamestate, new_move)

            # Create a new node for that move and connect it to the current node
            new_node = Node(new_state, False if new_state[1] % 2 else True, new_move, current_node)
            current_node.children.append(new_node)
            new_node.parent = current_node
            print(current_node.children)

            current_moves.remove(new_move)
            #current_state = new_state
            current_node = new_node

        current_node.N +=1

        if not is_winning:
            # Draw
            current_node.Q += 0 #TODO doet niks dus weghalen?
        elif current_node.black == self.black:
            # Win for own player
            current_node.Q += 1
        else:
            # Lose for own player
            current_node.Q -= 1

        self.backup_value(current_node)

    def backup_value(self, node: Node) -> None:
        print("backup_value")
        if node.parent is not None:
            print("backup_valuefsdjfkdsfjkahfgjksg")
            node.parent.Q += node.Q
            node.parent.N += 1
            self.backup_value(node.parent)

    """Calculate best move based on the available moves."""
    def calculate_best_move(self, node: Node) -> Tuple[Move, Node]:
        print("calculate_best_move")
        best_value = float('-inf')
        best_child = None

        print(f'{node.children} dit is deze zooi')

        for child in node.children:
            current_value = child.Q / child.N
            if current_value > best_value:
                best_value = current_value
                best_child = child

            print(best_value)

        return best_child.last_move, best_child


    # This function has a time complexity of O(1) because it instantly returns a value
    def id(self) -> str:
        """Please return a string here that uniquely identifies your submission e.g., "name (student_id)" """
        return "Emma Raijmakers (1784436)"


if __name__ == "__main__":
    p1 = EmmaPlayer(black_=True)
    GmQuickTests.testWinSelf1(p1)