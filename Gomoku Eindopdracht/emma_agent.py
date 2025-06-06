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

from competition import Competition
from random_agent import random_dummy_player
#from gomoku_ai_marius1_webclient import gomoku_ai_marius1_webclient
#from gomoku_ai_random_webclient import gomoku_ai_random_webclient

#TODO black = x = 1
#TODO white = o = 2

#TODO added to optimise: saving tree between moves, finished nodes added, early stop in roll out, linked list

# Class to save values for each node in the tree
class Node:
    def __init__(self, current_gamestate_: GameState, black_: bool, last_move_: Move = None, parent_: Node = None):
        self.current_gamestate = current_gamestate_

        self.black = black_

        self.last_move = last_move_

        self.parent = parent_
        self.children = []

        # Number of wins in children
        self.Q = 0

        # Number of visits to current node
        self.N = 0

        # Checks if this node is fully expended (win, lose or draw) 
        self.fully_expended = False

# Class for my Gomoku MCTS player
# The time complexity analysis is added in the comments of each function
class EmmaPlayer:
    """This class specifies a player that does MCTS.
    The use of this class is two-fold: 1) You can use it as a base random roll-out policy.
    2) it specifies the required methods that will be used by the competition to run
    your player
    """

    def __init__(self, black_: bool = True):
        """Constructor for the player.
        
        This function has a time complexity of O(1), because it happens instantly.
        """
        self.black = black_

        self.base_node = None

    def new_game(self, black_: bool):
        """At the start of each new game you will be notified by the competition.
        this method has a boolean parameter that informs your agent whether you
        will play black or white.

        This function has a time complexity of O(1), because it happens instantly.
        """
        self.black = black_

        self.base_node = None

    def move(self, state: GameState, last_move: Move, max_time_to_move: int = 1000) -> Move:
        """This is the most important method: the agent will get:
        1) the current state of the game
        2) the last move by the opponent
        3) the available moves you can play (this is a special service we provide ;-) )
        4) the maximum time until the agent is required to make a move in milliseconds [diverging from this will lead to disqualification].

        This function has a few loops. Each time 'in' is used, it loops through a list, which is linear and O(n). The second time 'in'
        is used, the 'index' function is also called, that looks through the children moves list. However, they happen after each other, 
        making that part of the code still O(n).

        After that, there is the while loop with a function call to the 'find_spot_to_expand' function that has a time complexity of
        O(n^3) (see that function for further explanation). The while loop keeps looping until the time runs out, making it linear
        and O(n), adding this to the 'find_spot_to_expand' function call makes a time complexity of O(n^4).

        Lastly, the 'calculate_best_move_and_child' has a time complexity of O(n) (see that function for further information).

        All the above mentioned code parts happen after each other. So, only the biggest time complexity matters for this function
        and that is O(n^4).
        """

        # Create a base node if it does not exist yet
        #if self.base_node is None:
            #self.base_node = Node(state, self.black, last_move)
        #Deactivate these comments when running all tests, to make sure every test has a new base node
        #else:
        self.base_node = Node(state, self.black, last_move)
        #

        # If the last move of the opponent already exists in the tree, set it as the current base node
        # If not, then create a new node

        #""" Activate these comments when running all tests
        # children_moves = []

        # for child in self.base_node.children: # The base node here is still our own last move
        #     children_moves.append(child.last_move)

        # if last_move in children_moves:
        #     self.base_node = self.base_node.children[children_moves.index(last_move)] # Index of the child is the same as the index in children_moves list
        # else:
        #     self.base_node = Node(state, self.black, last_move)
        #"""

        # Remove parents of current base node, so the backup function does not continue further than the current base node
        if self.base_node.parent is not None:
            self.base_node.parent = None

        # Expand tree in max time
        safe_time = 100     # 80 ms still causes disqualification, number higher than 80 ms
        max_time = time.time() + (max_time_to_move / 1000) - (safe_time / 1000)

        #for i in range(0,10000): # For debugging
        while time.time() < max_time:
            #new code \/ check also big O notation 
            # new_board = copy.deepcopy(state[0])
            # new_ply = copy.copy(state[1])
            # new_state = (new_board, new_ply)

            # self.find_spot_to_expand(new_state, self.base_node)

            self.find_spot_to_expand(state, self.base_node)

        # Calculate best move
        best_move, best_child = self.calculate_best_move_and_child(self.base_node)

        # Update the base node to our move, so the opponent move might be chosen from the tree in the next move
        self.base_node = best_child

        return best_move

    def find_spot_to_expand(self, state: GameState, current_node: Node) -> None:
        """Function to find a spot in the current tree to expend, that is not yet fully expanded.

        There are more parts in this function that can possibly influence the time complexity. The 'where' function in the 'valid_moves' 
        function loops over the 2D board. Because the board is 2D, searching in it is exponentially. Making it O(n^2). The for loop goes
        through all the children once, making it linear and O(n). Lastly when 'in' is used in this function, it looks through all
        children in the list, because the list is unsorted. This is also linear and O(n).
        
        There are also function calls to other functions. The function that is called with the highest time complexity is the 
        'roll_down' function, which is O(n^3). Other function calls and what is mentioned in the previous text, are not 
        added because these parts of the code happen after each other, so only the biggest matters. Therefore, the time 
        complexity of this function is O(n^3).
        """
        current_moves = gomoku.valid_moves(state)

        #TODO hier maak een list van alle moves waarvan de children nog niet fully expanded zijn en kies daar random uit????

        if len(current_moves) > 0: #TODO hier niet if len > 0 maar check if alle children fully expended zijn???
            new_move = random.choice(current_moves)

            # Check if the new move already exists in the children of the current base node
            children_moves = []

            for child in current_node.children:
                children_moves.append(child.last_move)

            # If not, create a new node with that move
            if new_move not in children_moves:
                new_node, is_winning, draw = self.simulate_move_and_return_new_node(current_node, new_move)

                # If the node is fully expended (win/lose/draw), update the N and Q values
                if new_node.fully_expended:
                    new_node.N += 1

                    # If there is a draw, current_node.Q += 0 -> nothing happens
                    if new_node.black == self.black and not draw:
                        new_node.Q += 1 # Win for own player
                    elif new_node.black != self.black and not draw:
                        new_node.Q -= 1 # Lose for own player

                    # Back up the N and Q values to parent nodes
                    self.backup_value(new_node, new_node.Q)

                # If the node is not fully expended, roll down the node
                else:
                    self.roll_down(new_node)

            # If the move exists in the children, find a new spot to extend, going from the existing child with the move
            elif new_move in children_moves and not current_node.children[children_moves.index(new_move)].fully_expended:
                new_base_node = current_node.children[children_moves.index(new_move)] # Move and child index are the same
                self.find_spot_to_expand(new_base_node.current_gamestate, new_base_node)

    def roll_down(self, node_to_roll_down:Node) -> None:
        """Function to roll down the node found by the expand function to a final state (win/lose/draw).

        There are more parts in this function that can possibly influence the time complexity. The 'where' function in the 'valid_moves' 
        function loops over the 2D board. Because the board is 2D, searching in it is exponentially. Making it O(n^2). The
        'simulate_move_and_return_new_node' function is O(n^2) (see that function for further information) and because
        it is called within the while loop, that loops linear and with O(n), this becomes O(n^3). Lastly, the 'backup_value' function 
        is O(n^2) (see that function for further information).

        These three parts run one after the other, so only the highest part is important. That is O(n^3).
        """
        current_moves = gomoku.valid_moves(node_to_roll_down.current_gamestate)
        current_node = node_to_roll_down

        draw = False

        # While the node is not fully expended and there are still moves available, roll down the node to an end state (win/lose/draw)
        while (not current_node.fully_expended) and len(current_moves) > 0:
            # Choose a random move from the current valid moves and play that move
            new_move = random.choice(current_moves)
            new_node, is_winning, draw = self.simulate_move_and_return_new_node(current_node, new_move)

            # Make sure a move in the roll down cannot be done more than once
            current_moves.remove(new_move)

            current_node = new_node

        # Update the N and Q values and back them up to parent nodes
        current_node.N +=1

        # If there is a draw, current_node.Q += 0 -> nothing happens
        if current_node.black == self.black and not draw:
            current_node.Q += 1 # Win for own player
        elif current_node.black != self.black and not draw:
            current_node.Q -= 1 # Lose for own player

        # Back up the N and Q values to parent nodes
        self.backup_value(current_node, current_node.Q)

    def simulate_move_and_return_new_node(self, node: Node, move: Move) -> (Node, bool, bool): # new_node, is_winning, draw
        """Function to simulate a new move and create a new node from it.

        This function has a time complexity of O(n^2), because most of the code happens instantly, but the 'deepcopy'
        function and 'in' (which is used twice) both need to go through the whole board. Because the board is 2D
        this grows exponentially and is O(n^2).
        """

        # Create a new gamestate from the given move to simulate and create a new node from it.
        is_valid, is_winning, new_state = gomoku.move(copy.deepcopy(node.current_gamestate), move)

        new_node = Node(new_state, False if new_state[1] % 2 else True, move, node)

        node.children.append(new_node)

        # Check if the new node is a winning move or a draw and set fully expanded to true based on that.
        if is_winning or not 0 in new_state[0]:
            new_node.fully_expended = True

        # To be sure, moves should be valid (according to gomoku.valid_moves function).
        if not is_valid:
            print("Move was not valid")

        # Return the new node, if the move was a winning move and if the move resulted in a draw
        return new_node, is_winning, (not 0 in new_state[0]) and (not is_winning)

    def backup_value(self, node: Node, q_value: int) -> None:
        """Function to back up the value from a child in a finished state (win/lose/draw) to the current base node.

        This function has more parts that can possibly influence the time complexity. Firstly, the recursion that backs 
        up a value from the end of the linked list to the beginning. It loops once over all items in a branch of the linked 
        list (tree) and therefore is linear and O(n). The same is true for the for-loop, which loops once over all the children
        in the list and is also linear and O(n). Lastly, the 'where' function in the 'valid_moves' function that
        loops over the 2D board. Because the board is 2D, searching in it is exponentially. Making it O(n^2).

        These three parts run one after the other, so only the highest part is important. So the time complexity
        of this function is O(n^2).
        """

        # If the current base node is not yet reached,
        # Back up the Q and N value to the parent of the current node and go to the parent node
        if node.parent is not None:
            node.parent.Q += q_value
            node.parent.N += 1
            self.backup_value(node.parent, q_value)

        # Back up the fully expended value from the children to the current node
        done = True
        for child in node.children:
            if not child.fully_expended:
                done = False

        # If all children of the current node are fully expended and all possible children exist
        # Then the current node is also fully expended
        if (len(node.children) == gomoku.valid_moves(node.current_gamestate)) and done:
            node.fully_expended = True

    def calculate_best_move_and_child(self, node: Node) -> Tuple[Move, Node]:
        """Function to calculate the best move based on the Q and N values in the children.

        This function has a time complexity of O(n), because it has to loop once over all the children
        that are unsorted to find the best value. This makes this function linear.
        """

        best_value = float('-inf')
        best_child = None

        # Calculate the value of each child and replace the best child and value, if a higher value is found
        for child in node.children:
            current_value = child.Q / child.N

            if current_value > best_value:
                best_value = current_value
                best_child = child

        return best_child.last_move, best_child

    def id(self) -> str:
        """Please return a string here that uniquely identifies your submission e.g., "name (student_id)."

        This function has a time complexity of O(1), because it instantly returns a value.
        """
        return "Emma Raijmakers (1784436)"


if __name__ == "__main__":
    p0 = EmmaPlayer(black_=True)

    for i in range(1):
        #GmQuickTests.testWinSelf1(p0)
        #GmQuickTests.testPreventWinOther1(EmmaPlayer(black_=True))
        GmQuickTests.doAllTests(p0)

    # # Run 10 competitions between my AI and the random AI
    # game = gomoku.starting_state()

    # p1 = random_dummy_player()
    # #p2 = gomoku_ai_marius1_webclient()
    # #p3 = gomoku_ai_random_webclient()

    # comp = Competition()
    # comp.register_player(p1)
    # comp.register_player(p0)

    # for i in range(10):
    #     comp.play_competition()
    #     comp.print_scores()
