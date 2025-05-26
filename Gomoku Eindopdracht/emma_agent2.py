from __future__ import annotations # Nodig voor type hinting (Node als member in Node)
import math
import random
import numpy as np
import gomoku
from gomoku import Move, GameState, Board, move, SIZE
import copy
import time
from typing import Tuple, List
from GmUtils import GmUtils
from GmQuickTests import GmQuickTests

from competition import Competition
from random_agent import random_dummy_player
#from gomoku_ai_marius1_webclient import gomoku_ai_marius1_webclient
#from gomoku_ai_random_webclient import gomoku_ai_random_webclient

# TODO toegevoegde optimalisaties: finished nodes, early stop in roll out, linked list, alleen moves zetten om al bestaande moves,
# moves opslaan in de node, list() ipv copy

# Class om waardes op te slaan voor iedere node in de tree
class Node:
    def __init__(self, current_gamestate_: GameState, black_: bool, last_move_: Move = None, parent_: Node = None):
        self.current_gamestate = current_gamestate_

        self.black = black_

        self.last_move = last_move_

        self.parent = parent_
        self.children = []

        # Nummer van wins in children
        self.Q = 0

        # Nummer van visits in current node
        self.N = 0

        self.valid_moves_for_expand = []

        self.valid_moves_for_rollout = []

# Class voor mijn Gomoku MCTS player
# De time complexity analysis is toegevoegd in de comments van iedere functie
class EmmaPlayer:
    """This class specifies a player that does MCTS.
    The use of this class is two-fold: 1) You can use it as a base random roll-out policy.
    2) it specifies the required methods that will be used by the competition to run
    your player
    """

    def __init__(self, black_: bool = True):
        """Constructor for the player.
        
        Deze functie heeft een time complexity van O(1), omdat het instantly gebeurt.
        """
        self.black = black_

        self.base_node = None

        self.number_of_rollouts = 10

        self.exploration_val = 1/math.sqrt(2)

    def new_game(self, black_: bool):
        """At the start of each new game you will be notified by the competition.
        this method has a boolean parameter that informs your agent whether you
        will play black or white.

        Deze functie heeft een time complexity van O(1), omdat het instantly gebeurt.
        """
        self.black = black_

        self.base_node = None

    def get_surrounding_moves(self, state: GameState) -> List[Move]:
        """Functie om de omliggende moves van de al bestaande moves van een board te krijgen.
        
        In deze functie wordt er geloopt over het board. Daarvoor worden 2 loops gebruikt, wat een time complexity 
        is van O(n^2). Als het board groter wordt, zorgt dit dus voor exponentiele groei. Binnen deze loop wordt ook 
        geloopt over de omliggende plaatsen, maar de omliggende plaatsen blijven constant dezelfde waarde (8) en 
        groeien niet als het board groter wordt. Hierdoor zorgt dit er niet voor dat de time complexity hoger wordt.
        """

        board = state[0]
        ply = state[1]

        # Als er nog niks op het board ligt, dan mag alleen de move op de middelse positie 
        if ply == 1:
            middle = np.array(np.shape(board)) // 2
            return [tuple(middle)]
        
        else:
            moves = []

            # De omliggende posities van een move
            places_to_add = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

            board_size = len(board[0])

            # Loop door het board en vind alle posities die niet leeg zijn
            for i in range(board_size):
                for j in range(board_size):
                    if (board[i][j] != 0):
                        #Loop door alle omliggende posities
                        for y, x in places_to_add:

                            y_to_check = i + y
                            x_to_check = j + x

                            # Voeg een move toe als het binnen het board ligt, niet al toegevoegd is en niet al bezet is
                            if (0 <= y_to_check < board_size) and (0 <= x_to_check < board_size) and (not (y_to_check, x_to_check) in moves) and (board[y_to_check][x_to_check] == 0):
                                moves.append((y_to_check, x_to_check))

            return moves

    def move(self, state: GameState, last_move: Move, max_time_to_move: int = 1000) -> Move:
        """This is the most important method: the agent will get:
        1) the current state of the game
        2) the last move by the opponent
        3) the available moves you can play (this is a special service we provide ;-) )
        4) the maximum time until the agent is required to make a move in milliseconds [diverging from this will lead to disqualification].

        In deze functie worden de andere functies aageroepen. Als eerste de 'get_surrounding_moves' functie die een time complexity
        heeft van O(n^2) (zie functiebeschrijving van die functie). Vervolgens de shuffle functie die liniear door de list loopt en 
        daardoor O(n) is.

        Daarna is er een while loop waarin andere functies worden aangeroepen. De while loop blijft doorgaan tot een bepaalde tijd
        en is hierdoor liniear, O(n). Daarin wordt de 'find_spot_to_expand' functie aangeroepen die een time complexity van O(n^2) 
        (zie functiebeschrijving) heeft. In het if statement wordt de 'backup_value' functie van O(n) aangeroepen binnen een for loop. 
        Echter deze for loop heeft een vaste grootte, is hierdoor constant en voegt daarom niet toe aan een hogere time complexity. 
        Als laatste worden er in de while loop in de if statement de 'roll_out' functie, O(n^2) (zie functiebeschrijving) en nog eens 
        de 'backup_value', O(n) functie aangeroepen. Dit gebeurt allemaal na/afzonderlijk van elkaar in de while loop. Hierdoor is 
        alleen de hoogste time complexity de worst case in de while loop en dat is O(n^2) + de while loop O(n) = O(n^3).

        Onderaan de functie wordt nog de 'calculate_best_move_and_child' functie aangeroepen, maar die heeft een time complexity
        van O(n) en is dus niet hoger dan O(n^3) dus de time complexity van deze functie is O(n^3).
        """

        #TODO check alle comments en big O

        #TODO check of het kan werken met een leeg board/vol board

        # Maak de base node van de tree
        self.base_node = Node(state, self.black, last_move)

        # Vind de huidige valid moves, randomize en sla ze op in de base node
        self.base_node.valid_moves_for_expand = self.get_surrounding_moves(state)
        random.shuffle(self.base_node.valid_moves_for_expand)
        self.base_node.valid_moves_for_rollout = list(self.base_node.valid_moves_for_expand)

        # Expand tree in max time
        safe_time = 100     # 80 ms nog steeds disqualificatie, dus nummer hoger dan 80 ms
        max_time = time.time() + (max_time_to_move / 1000) - (safe_time / 1000)

        #for i in range(0,1000): # Voor debugging
        while time.time() < max_time:

            node_to_expand, already_terminal, win_in_one = self.find_spot_to_expand(state, self.base_node)

            # Als er een terminal node is gevonden, verander de value van de node gebaseerd op
            # of de eigen speler wint of verliest
            if already_terminal: #TODO kan dit makkelijker???
                if self.black == (node_to_expand.current_gamestate[1] % 2 == 0): #win voor eigen speler
                    # Backup het aantal keer als er roll outs worden gedaan
                    for i in range(self.number_of_rollouts):
                        self.backup_value(node_to_expand, 1)

                elif self.black != (node_to_expand.current_gamestate[1] % 2 == 0): #lose voor eigen speler
                    # Backup het aantal keer als er roll outs worden gedaan
                    for i in range(self.number_of_rollouts):
                        self.backup_value(node_to_expand, -1)

            # Als er een node wordt gevonden die gelijk wint, return dan de move van die node    
            elif win_in_one:
                return node_to_expand.last_move
            
            else:
                for i in range(self.number_of_rollouts):
                    val = self.roll_out(node_to_expand) 
                    self.backup_value(node_to_expand, val)

        # Bereken beste move
        best_move, best_child = self.calculate_best_move_and_child(self.base_node, False)
        return best_move
        
    def find_spot_to_expand(self, state: GameState, current_node: Node) -> Tuple[Node, bool, bool]:
        """Functie om een spot in de tree te vinden die nog niet fully expanded is.

        De code is verdeeld in 3 blokken die allemaal voor een andere situatie zorgen bij deze functie. De 3 blokken worden 
        hieronder besproken. De time complexity van de standaard python functies die zijn gebruikt, is hier terug te vinden: 
        https://wiki.python.org/moin/TimeComplexity 

        1. Alle code die binnen het eerste if statement staat gebeurt instant en heeft dus een time complexity van O(1).
        De 'isWinningMove' functie voert een check uit van if statements en is dus ook instant.

        2. Dan is er het tweede if statement. Het kopiëren van de gamestate bestaat o.a. uit het kopiëren van een 2D list. 
        Dit is exponentieel en dus O(n^2). De aanroep van de functie 'get_surrounding_moves' is O(n^2) (zie de functiebeschrijving 
        van deze functie). De shuffle functie loopt 1x door de list heen en is dus O(n). Dit gebeurt allemaal na elkaar dus alleen 
        de hoogste time complexity heeft de meeste invloed dus dat is O(n^2).

        3. Als laatste de 'calculate_best_move_and_child' functie die O(n) is (zie de functiebeschrijving van deze functie) en de
        recursieve aanroep van deze functie. De recursie loopt door een branch van de tree, wat liniear gebeurt en dus ook O(n) is.
        Deze twee dingen gebeuren na elkaar dus dit deel blijft O(n).

        Doordat in deze functie de 3 blokken apart van elkaar gebeuren is de worst case van deze functie het deel met de hoogste
        time complexity en dat is O(n^2).
        """

        # Check of er een last move is (1e ronde heeft geen last move)
        if(len(current_node.last_move) != 0):
            # Return de node terminal is die teriminal is (last move is winning of gelijk gespeeld (hele board staat vol)).
            if (GmUtils.isWinningMove(current_node.last_move, current_node.current_gamestate[0])) or (current_node.current_gamestate[1] > (SIZE * SIZE)):
                return current_node, True, False 

        # Als er voor de node nog children zijn om aan te maken
        if not len(current_node.valid_moves_for_expand) == 0:
            # Maak de state aan voor de nieuwe node
            new_move = current_node.valid_moves_for_expand[0]     
            is_valid, is_winning, new_state = gomoku.move(copy.deepcopy(current_node.current_gamestate), new_move)

            if not is_valid:
                print("Move was not valid")

            # Maak de nieuwe node en zorg dat de parents/children van beide nodes goed zijn
            new_node = Node(new_state, (new_state[1] % 2) == 1, new_move, current_node)
            current_node.children.append(new_node)

            # Bepaal voor de nieuwe node welke children en moves die kan hebben
            new_valid_moves = self.get_surrounding_moves(new_state)
            random.shuffle(new_valid_moves)
            new_node.valid_moves_for_expand = new_valid_moves

            new_node.valid_moves_for_rollout = list(new_valid_moves)

            # Verwijder de nieuwe child van de parent's nog aan te maken children
            current_node.valid_moves_for_expand.pop(0)

            # Als er een winnende child is
            if is_winning and current_node.parent == None:
                return new_node, False, True
            else:
                return new_node, False, False
        
        # Als er van een node al alle children zijn aangemaakt, bereken dan het beste child
        # en roep de functie opnieuw aan voor het child
        best_move, best_child = self.calculate_best_move_and_child(current_node, True)
        return self.find_spot_to_expand(best_child.current_gamestate, best_child)

    def roll_out(self, node_to_roll_down:Node) -> int:
        """Functie om de node die gevonden is in de expand functie naar beneden te rollen naar een final state (win/lose/draw).

        In deze functie zijn er meer delen die de time complexity kunnen beïnvloeden. Ten eerste is er een copy van de gamestate.
        Deze gamestate bestaat o.a. uit een 2D list. Het kopiëren hiervan is exponentieel en dus O(n^2). Daarnaast is er de while
        loop die doorgaat tot er een end state is (win/lose/draw) met in die while loop, een remove functie die time complexity
        O(n) heeft. Dit samen is ook O(n^2). Deze twee dingen gebeuren na elkaar, waardoor de gehele functie O(n^2) blijft. De rest 
        van de code gebeurt instantly en heeft door de al bestaande hogere time complexity, dus geen invloed.

        Voor de time complexity van de copy en remove functies is de volgende link gebruikt: https://wiki.python.org/moin/TimeComplexity
        """
        current_moves = list(node_to_roll_down.valid_moves_for_rollout)
        current_node = node_to_roll_down

        is_winning = False

        copy_gamestate = copy.deepcopy(current_node.current_gamestate)

        # Als er nog geen win of draw is in de node, roll down de node tot een end state (win/lose/draw)
        while (not is_winning) and len(current_moves) > 0:
            # Kies een random move van de huidige moves en speel die
            new_move = random.choice(current_moves)

            is_valid, is_winning, new_state = gomoku.move(copy_gamestate, new_move) 
            copy_gamestate = new_state

            if not is_valid:
                print("Move was not valid")

            # Zorgt ervoor dat een move in de roll down niet meer dan 1x gedaan kan worden
            current_moves.remove(new_move)

        # Return de value gebaseerd op het resultaat van de roll out
        if not is_winning: #draw
            return 0
        elif is_winning and (self.black == (new_state[1] % 2 == 0)): #win voor eigen speler
            return 1
        elif is_winning and (self.black != (new_state[1] % 2 == 0)): #lose voor eigen speler
            return -1

    def backup_value(self, node: Node, q_value: int) -> None:
        """Functie om de value van een child in een finished state (win/lose/draw) te backuppen naar de huidige base node.

        Deze functie backt een value up van een eind node naar de base node (heeft geen parent). Nodes zijn met elkaar 
        verbonden door een linked list (parent en child hebben een verwijzing naar elkaar). Het loopt een keer over 
        alle nodes in een branch van de tree en is daardoor liniear en heeft een time complexity van O(n).
        """
        current_node = node

        # Als de base node (geen parent) nog niet is bereikt,
        # back up de Q en N values naar de parent van de huidige node en ga naar de parent
        while current_node is not None:
            current_node.N += 1
            current_node.Q += q_value

            current_node = current_node.parent

    def calculate_best_move_and_child(self, node: Node, using_exploration: bool) -> Tuple[Move, Node]:
        """Functie om de beste move te berekenen gebaseerd op de Q en N values in de children.

        Deze functie heeft een time complexity van O(n), omdat het 1x loopt over alle children die
        ongesorteerd zijn om de beste value te vinden. Dit zorgt ervoor dat deze functie liniear is.
        """

        best_value = float('-inf')
        best_child = None
        factor = 1

        # Bereken de factor om de waarde van het kind mee te vermenigvuldigen
        if node.black == self.black: # Huidige zet is van eigen speler
            factor = 1
        elif node.black != self.black: # Huidige zet is van andere speler
            factor = -1

        # Bereken de value van iedere child en verander de beste child en value, als er een hogere value is gevonden
        for child in node.children:
            # Gebruik de exploration in de 'find_spot_to_expand' functie om een child te vinden om verder te expanden
            if using_exploration:
                current_value = (child.Q * factor) / child.N + self.exploration_val * math.sqrt((2 * np.log(node.N)) / child.N)
            # Gebruik het niet om de beste child te berekenen van de base node om de volgende move te doen
            else:
                current_value = (child.Q * factor) / child.N

            if current_value > best_value:
                best_value = current_value
                best_child = child

        return best_child.last_move, best_child

    def id(self) -> str:
        """Please return a string here that uniquely identifies your submission e.g., "name (student_id)."

        Deze functie heeft een time complexity van O(1), omdat het instantly gebeurt.
        """
        return "Emma Raijmakers (1784436)"


if __name__ == "__main__":
    p0 = EmmaPlayer(black_=True)

    random.seed(0)

    for i in range(1):
        #GmQuickTests.testWinSelf1(p0)
        random.seed(0)
        #GmQuickTests.testPreventWinOther1(p0)

        GmQuickTests.doAllTests(p0)


    # # Run 10 competitions between my AI and the random AI
    # game = gomoku.starting_state()

    # p1 = random_dummy_player()
    # # #p2 = gomoku_ai_marius1_webclient()
    # # #p3 = gomoku_ai_random_webclient()

    # comp = Competition()
    # comp.register_player(p1)
    # comp.register_player(p0)

    # for i in range(10):
    #     comp.play_competition()
    #     comp.print_scores()
