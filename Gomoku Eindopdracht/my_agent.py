import random
import gomoku
import time
import numpy as np
from gomoku import Board, Move, GameState
from GmUtils import GmUtils
import copy
from GmQuickTests import GmQuickTests

#TODO wanneer tree weer opnieuw maken/clearen?

#TODO werkt alles ook als mijn AI als wit speelt?

#TODO check of the algoritmes van de opracht kloppen met die in de reader

#TODO kijk of je copy's/deepcopy's weg kan halen -> of vervangen door snellere TODO voor onderzoek ook

#TODO die ene formule toevoegen, waar? best_move?

#This function has a time complexity of O(n^2) because the board (2D array) needs to be copied (maybe faster depending on the deepcopy function), 
#the other code is O(n) because it happens instantly
def play(game_state, move): ##move is a tuple indicating where the player to move is going to place a stone
        if (game_state[1] % 2 == 1):
            new_stone = 1 # black
        else:
            new_stone = 2 # white
        new_board = copy.deepcopy(game_state[0])
        new_game_state = ( new_board, game_state[1]+1)
                                                    #row    #col
        if(GmUtils.isValidMove(new_game_state[0], move[0], move[1])): #< TODO check of row en col niet omgewisseld moeten
            GmUtils.addMoveToBoard(new_game_state[0], move, new_stone)
        else:
            return None #invalid move
        return new_game_state

#This function has a time complexity of TODO
def calculate_best_move(node):
    best_value = node.children[0].Q / node.children[0].N
    best_move = node.children[0].last_move #TODO wat is last move hier en kan dat gebruikt worden?
    for i in range(1, len(node.children)):
        current_value = node.children[0].Q / node.children[0].N
        if (current_value > best_value):
            best_value = current_value
            best_move = node.children[i].last_move
    return best_move

class my_agent:

    def __init__(self, gstate, parentNode=None, last_move=None, valid_move_list=None, black_: bool = True):
        """Constructor for the player."""
        self.state=gstate
        self.board = gstate[0]
        #print(self.board)
        Board = gstate[0]
        self.won = None #<- TODO als dit werkt kun je er ook gewoon false in gooien?
        self.parent=parentNode
        self.children=[] #TODO voor onderzoek probeer andere container
        self.last_move = last_move
        print(Board)
        self.finished = GmUtils.isWinningMove(last_move, Board)
        self.Q = 0 #number of wins
        self.N = 0 #number of visits
        self.valid_moves = valid_move_list

        self.black = black_

    def new_game(self, black_: bool):
        """At the start of each new game you will be notified by the competition.
        this method has a boolean parameter that informs your agent whether you
        will play black or white.
        """
        self.black = black_
        
    #This function has a time complexity of O(1) because it instantly calculates and returns a value
    def fully_expanded(self):
        return len(self.children) is len(self.valid_moves)
    

    #This function has a time complexity of TODO
    def expand(self,move,n_rollouts): #TODO number of expantions voor onderzoek
        #when expanding a node with a new child node, we are not also going to perform a number of roll-outs.
        #first, we create the new node:
        new_state = play(self.state, move)
        if(new_state is None):
            return
        new_valid_moves = copy.deepcopy(self.valid_moves)
        new_valid_moves.remove(move)
        new_node = my_agent(new_state, parentNode=self, last_move=move,valid_move_list=new_valid_moves, black_=self.black) #TODO hier self.black??
        #add it to the children:                                                                                                #of tegenovergestelde?
        self.children.append(new_node)                                                                                          #of maakt niet uit (gebeurd al in andere functie?)
        #and then perform a number of random roll-outs: random plays until the game finishes                                    #in andere functies aanpassen naar self.black??
        for i in range(n_rollouts):
            score = new_node.roll_out()
            #and process the result (score) we get from this rollout
            new_node.process_result(score)

    #This function has a time complexity of O(n) because the valid moves need to be copied and shuffled (again maybe less depending on the functions) 
    #and moves need to be played until someone wins (worst case until the whole board is full/all valid moves are played), which is also O(n).
    #Furthermore, the TODO check who won function is called which has a time complexity of TODO
    #This results in O(n) + O(n) + TODO which is a time complexity of O(n)
    def roll_out(self):
        #rollouts are quite simple
        #when the node respresents a game state of a game that's finished, we immediately return the result
        if(self.finished):
            if(self.won == 1):
                return 1
            elif(self.won == 2):
                return -1
            else:
                return 0
        #else we play moves in on the remaining open fields
        moves = copy.deepcopy(self.valid_moves) #TODO is hier de copy functie voldoende??? ja?
        #TODO voor onderzoek zetten niet random, maar bv rondom vorige zet
        random.shuffle(moves) #TODO wat is time complexity van shuffle functie -> opzoeken
        new_state = self.state
        for move in moves:
            new_state = play(new_state, move)
            #print(Board)
            fin_win = GmUtils.isWinningMove(move, new_state[0]) #TODO hier Board ipv new_state[0]?

            if(new_state[1] % 2 == 0):
                whowon = 1 #TODO klopt dit of omgedraait? als deelbaar door 2 dan vorige zet gedaan door zwart(1), zwart == 2?!?
            else:
                whowon = 2

            #TODO gelijkspel geeft niet goed 0 terug??

            #until the game finishes, and return the score:
            if(fin_win):
                if(whowon == 1 and self.black):
                    print(f'whowon: {whowon}, self.black: {self.black}')
                    return 1
                elif(whowon == 1 and not self.black):
                    print(f'whowon: {whowon}, self.black: {self.black}')
                    return -1
                elif(whowon == 2 and not self.black):
                    print(f'whowon: {whowon}, self.black: {self.black}')
                    return 1
                elif(whowon == 2 and self.black):
                    print(f'whowon: {whowon}, self.black: {self.black}')
                    return -1
                else:
                    print(f'whowon: {whowon}, self.black: {self.black}')
                    return 0

            # if(len(moves) == 0):
            #     return 0
        
    #This function has a time complexity of O(1) because calculations happen instantly
    def process_result(self,rollout_result): #TODO voor onderzoek probeer formule uit reader bij opdracht
        #then we increase Q by the score, and N by 1
        print(rollout_result)
        self.Q+=rollout_result #TODO check even of klopt met algoritme 24, als beurt van tegenstander dan - result, ja add dit?? <- gedaan hierboven genoeg?
        self.N+=1
        #and do the same, recursively, for its ancestors
        if(self.parent is not None): 
            self.parent.process_result(rollout_result)

    #This function has a time complexity of TODO
    def move(
        self, state: GameState, last_move: Move, max_time_to_move: int = 1000
    ) -> Move:
        """This is the most important method: the agent will get:
        1) the current state of the game
        2) the last move by the opponent
        3) the available moves you can play (this is a special service we provide ;-) )
        4) the maximum time until the agent is required to make a move in milliseconds [diverging from this will lead to disqualification].
        """
        #to make sure move is chosen within the given time 
        safe_time = 100 #TODO voor onderzoek experiment met dit

        max_time = time.time() + max_time_to_move - safe_time
        cur_time = time.time() #TODO deze var niet nodig?
        
        #TODO add function calls to other functions here
        #TODO add system to make sure not to exceed max time, add max time to expand function??
        
        moves = gomoku.valid_moves(state)
        random.shuffle(moves)

        best_move = moves[0] #TODO niet nodig? wat als niet genoeg tijd voor 1 expand?

        expand_value = 100 #TODO voor onderzoek, verander deze waarde

        root = my_agent(state, last_move=self.last_move, valid_move_list=moves) #TODO hier ook toevoegen of als black of white speelt

        for mv in root.valid_moves:
            root.expand(mv, expand_value)
            cur_time = time.time()
            if cur_time > max_time:
                break

        best_move = calculate_best_move(root)

        return best_move

    #This function has a time complexity of O(1) because it instantly returns a value
    def id(self) -> str:
        """Please return a string here that uniquely identifies your submission e.g., "name (student_id)" """
        return "Emma Raijmakers (1784436)"


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
        if len(moves) == 1:
            return moves[0]
        else:
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
            # print(current_board)
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

def testing():

    gamestate = (
            np.array(
                [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [2, 0, 0, 0, 0, 0, 0],
                    [2, 0, 0, 0, 0, 0, 0],
                    [2, 0, 0, 0, 0, 0, 0],
                    [2, 0, 0, 0, 0, 0, 0],
                ]
            ),
            5,
        )

    valid_moves = gomoku.valid_moves(gamestate)

    p1 = my_agent(gamestate, parentNode=None, last_move=(6,6), valid_move_list=valid_moves, black_=True)
    GmQuickTests.testWinSelf1(p1)

testing()
