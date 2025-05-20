from __future__ import annotations # Needed for type hinting (Node as member in Node)
import math
import random
import numpy as np
import gomoku
from gomoku import Move, GameState, Board, move
import copy
import time
from typing import Tuple, List
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

        self.valid_moves_for_expand = []

        self.valid_moves_for_rollout = []

        # Checks if this node is fully expanded (win, lose or draw) 
        #self.fully_expanded = False

        #TODO 2 sets met valid moves van node en valid moves to play (welke kinderen bestaan al?) moves 1x shuffle

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

        self.number_of_rollouts = 10

        self.exploration_val = 1/math.sqrt(2) #TODO deze waarde veranderen nog??

    def new_game(self, black_: bool):
        """At the start of each new game you will be notified by the competition.
        this method has a boolean parameter that informs your agent whether you
        will play black or white.

        This function has a time complexity of O(1), because it happens instantly.
        """
        self.black = black_

        self.base_node = None

    def get_surrounding_moves(self, state: GameState) -> List[Move]:
        board = state[0]
        ply = state[1]
        if ply == 1:
            middle = np.array(np.shape(board)) // 2
            return [tuple(middle)]
        else:
            moves = []
            places_to_add = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

            board_size = len(board[0])

            for i in range(board_size):
                for j in range(board_size):
                    if (board[i][j] != 0):
                        for y, x in places_to_add:

                            y_to_check = i + y
                            x_to_check = j + x

                            if (0 <= y_to_check < board_size) and (0 <= x_to_check < board_size) and (not (y_to_check, x_to_check) in moves) and (board[y_to_check][x_to_check] == 0):
                                moves.append((y_to_check, x_to_check))

            return moves

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

        #TODO memoisatie eruit slopen
        #TODO check alleen de spots die rondom the huidige stenen staan
        #TODO experimenteer met exploration val
        #TODO check alle comments en big O

        self.base_node = Node(state, self.black, last_move)

        self.base_node.valid_moves_for_expand = self.get_surrounding_moves(state)
        random.shuffle(self.base_node.valid_moves_for_expand)

        self.base_node.valid_moves_for_rollout = gomoku.valid_moves(state)

        # Expand tree in max time
        safe_time = 100     # 80 ms still causes disqualification, number higher than 80 ms
        max_time = time.time() + (max_time_to_move / 1000) - (safe_time / 1000)

        for i in range(0,100000): # For debugging
        #while time.time() < max_time:

            node_to_expand, already_terminal, win_in_one = self.find_spot_to_expand(state, self.base_node)

            #TODO kan dit makkelijker???
            if already_terminal:
                if self.black == (node_to_expand.current_gamestate[1] % 2 == 0): #win for self
                    #node_to_expand.Q += (self.number_of_rollouts)
                    for i in range(self.number_of_rollouts):
                        self.backup_value(node_to_expand, 1)

                elif self.black != (node_to_expand.current_gamestate[1] % 2 == 0): #lose for self
                    #node_to_expand.Q -= (self.number_of_rollouts)
                    for i in range(self.number_of_rollouts):
                        self.backup_value(node_to_expand, -1)
                
            elif win_in_one:
                return node_to_expand.last_move
            
            else:
                for i in range(self.number_of_rollouts):
                    val = self.roll_out(node_to_expand) 
                    self.backup_value(node_to_expand, val)

        # Calculate best move
        best_move, best_child = self.calculate_best_move_and_child(self.base_node, False)
        return best_move
        
    def find_spot_to_expand(self, state: GameState, current_node: Node) -> Tuple[Node, bool, bool]:
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

        if (GmUtils.isWinningMove(current_node.last_move, current_node.current_gamestate[0])) or (len(current_node.valid_moves_for_expand) == 0):
            return current_node, True, False 

        #current_moves = gomoku.valid_moves(state) #TODO waar valid moves bijhouden en moves verwijderen als ze al gedaan zijn?

        #TODO de valid moves opslaan in de node

        #TODO werkt dit zo???
        # for child in current_node.children:
        #     if child.last_move in current_moves:
        #         current_moves.remove(child.last_move)
        
        # if len(current_moves) == 0: 
        #     current_node.fully_expanded = True

        #if not current_node.fully_expanded:
        if not len(current_node.valid_moves_for_expand) == 0:
            new_move = current_node.valid_moves_for_expand[0]
            
            is_valid, is_winning, new_state = gomoku.move(copy.deepcopy(current_node.current_gamestate), new_move)

            if not is_valid:
                print("Move was not valid")

            new_node = Node(new_state, (new_state[1] % 2) == 1, new_move, current_node)
            current_node.children.append(new_node)

            new_node.valid_moves_for_rollout = copy.deepcopy(current_node.valid_moves_for_rollout)
            new_node.valid_moves_for_rollout.remove(new_move)

            new_valid_moves = copy.deepcopy(current_node.valid_moves_for_expand) #TODO hier copy of deepcopy???
            new_valid_moves.pop(0)
            new_node.valid_moves_for_expand = new_valid_moves

            current_node.valid_moves_for_expand.pop(0)

            if is_winning and current_node.parent == None:
                return new_node, False, True
            else:
                return new_node, False, False
        

        best_move, best_child = self.calculate_best_move_and_child(current_node, True)
        return self.find_spot_to_expand(best_child.current_gamestate, best_child)

    def roll_out(self, node_to_roll_down:Node) -> int:
        """Function to roll down the node found by the expand function to a final state (win/lose/draw).

        There are more parts in this function that can possibly influence the time complexity. The 'where' function in the 'valid_moves' 
        function loops over the 2D board. Because the board is 2D, searching in it is exponentially. Making it O(n^2). The
        'simulate_move_and_return_new_node' function is O(n^2) (see that function for further information) and because
        it is called within the while loop, that loops linear and with O(n), this becomes O(n^3). Lastly, the 'backup_value' function 
        is O(n^2) (see that function for further information).

        These three parts run one after the other, so only the highest part is important. That is O(n^3).
        """
        #current_moves = gomoku.valid_moves(node_to_roll_down.current_gamestate)
        current_moves = copy.deepcopy(node_to_roll_down.valid_moves_for_rollout) #TODO is dit sneller dan valid_moves???
        current_node = node_to_roll_down

        draw = False
        is_winning = False
        finished = False

        copy_board = copy.deepcopy(current_node.current_gamestate[0])
        copy_gamestate = (copy_board, current_node.current_gamestate[1])

        # While the node is not fully expanded and there are still moves available, roll down the node to an end state (win/lose/draw)
        while (not finished) and len(current_moves) > 0: #TODO while s not terminal ???????
            # Choose a random move from the current valid moves and play that move
            new_move = random.choice(current_moves)

            is_valid, is_winning, new_state = gomoku.move(copy_gamestate, new_move)  

            if not is_valid:
                print("Move not valid")

            #new_node = Node(new_state, False if new_state[1] % 2 else True, new_move, current_node)
            #current_node.children.append(new_node)

            if is_winning or (not 0 in new_state[0]):
                finished = True

            #new_node, is_winning, draw = self.simulate_move_and_return_new_node(current_node, new_move)

            # Make sure a move in the roll down cannot be done more than once
            current_moves.remove(new_move)

            #current_node = new_node

                            #TODO dit deel is niet nodig???
        if not is_winning: #and (not 0 in copy_gamestate[0]): #draw
            return 0
        elif is_winning and (self.black == (new_state[1] % 2 == 0)): #win for self TODO check hier of statement klopt
            return 1
        elif is_winning and (self.black != (new_state[1] % 2 == 0)): #lose for self
            return -1

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
        current_node = node

        # If the current base node is not yet reached,
        # Back up the Q and N value to the parent of the current node and go to the parent node
        while current_node is not None:
            current_node.N += 1
            current_node.Q += q_value

            current_node = current_node.parent

    def calculate_best_move_and_child(self, node: Node, using_exploration: bool) -> Tuple[Move, Node]:
        """Function to calculate the best move based on the Q and N values in the children.

        This function has a time complexity of O(n), because it has to loop once over all the children
        that are unsorted to find the best value. This makes this function linear.
        """

        best_value = float('-inf')
        best_child = None
        factor = 1

        # Calculate the factor by which to multiply the value of a child
        if node.black == self.black: # Current turn is for own player
            factor = 1
        elif node.black != self.black: # Current turn is for opponent
            factor = -1

        # Calculate the value of each child and replace the best child and value, if a higher value is found
        for child in node.children:
            if using_exploration:
                current_value = (child.Q * factor) / child.N + self.exploration_val * math.sqrt((2 * np.log(node.N)) / child.N)
            else:
                current_value = (child.Q * factor) / child.N

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
