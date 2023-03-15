'''
Yangbot #2 - elo ~ 1800 - 2000

FEATURE LIST:
- UCI interface                         [INCOMPLETE]
- opening book                          [OK]
- negamax                               [OK]
- quiscence search                      [OK]
- killer moves                          [TESTING]
- move ordering                         [TESTING]
    > MVV LVA                           [OK]
- PST                                   [OK]
- PV                                    [OK]
- evaluation                            [TESTING]
    > PeSTO evaluation                  [OK]
    > Incremental material counting     [INCOMPLETE]
- iterative deepening                   [OK]
- null moves                            [TESTING]
- late move reduction                   [TESTING]
- transposition tables                  [GOOD]
- mate distance pruning                 [TESTING]
- razoring                              [INCOMPLETE]
- check extensions                      [INCOMPLETE]

CHANGE LOGS:

- added mate distance pruning - however it seems to mess up move ordering so i made alpha and beta temporary variables
- moved outcomes from evaluation to search
- ~piece has more priority than psqt~ Tests found that equal play is superior

weaknesses:
- prioritises trading when it is better to attack the king
- increase speed and depth ~ try to reach depth, avg depth is 5 atm
    MAYBE USE CYTHON?
    MAYBE PRUNE MORE BRANCHES (killer huristics not confirmed to work)
    TEST NEW HASH TABLES?

'''


import chess
import chess.polyglot
from chessUtil import Piece_Square_Tables
import random
import cProfile
import pstats
import settings
import threading
import requests
import time

class HashEntry:

    NONE = 0
    EXACT = 1
    BETA = 2
    ALPHA = 3

    def __init__(self):
        self.key = ""
        self.move = None
        self.score = 0
        self.depth = 0
        self.flag = HashEntry.NONE


# bot class
class BOT():

    INFINITY = 137000000
    hashes = {}
    hash_table = {}
    pv_table = {}
    contempt = [5, 2.5, 0]


    def __init__(self):


    
        self.saved_moved = ""
        self.results = []


        self.clear_search_params()


        self.Mvv_Lva_Victim_scores = {
            "p" : 100,
            "n" : 200,
            "b" : 300,
            "r" : 400,
            "q" : 500,
            "k" : 600
        }

        # init mvv lva
        #self.Mvv_Lva_Scores = {}
        #for attacker in self.Mvv_Lva_Victim_scores.keys():
        #    self.Mvv_Lva_Scores[attacker] = {}
        #    for victim in self.Mvv_Lva_Victim_scores.keys():
        #        self.Mvv_Lva_Scores[attacker][victim] = int(self.Mvv_Lva_Victim_scores[victim] + 6  - (self.Mvv_Lva_Victim_scores[attacker] / 100)) + 1000000



    ############################## UTILITY FUNCTIONS ##############################

    def clear_search_params(self):
        self.nodes = 0
        #self.pv_table = {}
        self.killers = {0: {}, 1: {}}

        for i in range(0, 400):
            self.killers[0][i] = None
            self.killers[1][i] = None

        self.search_history = {}

        for i in range(0, 64):
            self.search_history[i] = {}
            for ii in range(0, 64):
                self.search_history[i][ii] = 0

    def get_opening_move(self, board):

        max_weight = 0
        max_move = None

        found_moves = {}

        with chess.polyglot.open_reader("chessAI/data/polyglot/performance.bin") as reader:
            for entry in reader.find_all(board):

                if not entry.weight in found_moves:
                    found_moves[entry.weight] = []

                found_moves[entry.weight].append(entry.move)

                if entry.weight > max_weight:
                    max_weight = entry.weight
                    max_move = entry.move

        # shuffle out of best moves

        if max_move is None:
            return None

        best_moves = found_moves[max_weight]

        random.shuffle(best_moves)

        return best_moves[0]

    def getPhase(self, board):
        l = len(board.piece_map())

        if 20 <= l <= 32:
            return 0
        elif 10 <= l < 20:
            return 1
        else:
            return 0

    def store_hash(self, pos, move, score, flag, depth):
        he = HashEntry()
        he.key = pos
        he.move = move
        he.score = score
        he.flag = flag
        he.depth = depth

        BOT.hash_table[pos] = he


    def get_hash(self, pos):

        if pos in BOT.hash_table:
            return BOT.hash_table[pos]

        return None

    def store_pvline(self, position_hash, move):
        BOT.pv_table[position_hash] = move


    def get_pvline(self, position_hash, turn):
        if position_hash not in BOT.pv_table:
            return None

        return BOT.pv_table[position_hash]

    def retrieve_pvline(self, board):

        pv_line = list()

        _b = board.copy()

        for _ in range(10000):
            #h = self.cu.get_board_hash_pychess(_b)
            h = _b.fen()
            hash_entry = self.get_hash(h)



            if hash_entry is not None and hash_entry.flag == HashEntry.EXACT:
                pv_line.append(hash_entry.move)
                _b.push(hash_entry.move)
            else:
                break

        return pv_line

    def get_pv_line_san(self, board, line):
        san_list = list()
        b = board.copy()

        for move in line:
            san_list.append(b.san(move))
            b.push(move)

        return san_list

    ############################ EVALUATION AND SEARCH ################################
    @staticmethod
    def evaluate_EVAL(board):

        #if board.is_checkmate():
        #    return -1 * (BOT.INFINITY - board.ply())
        #elif board.is_stalemate() or board.is_repetition() or board.is_insufficient_material():
        #   return 0
        
        mg, eg, phase = 0, 0, 0

        #bq, wq = (len(board.pieces(chess.QUEEN, chess.BLACK)) > 0), (len(board.pieces(chess.QUEEN, chess.WHITE)) > 0)

        pieces = board.piece_map()

        for pos, _piece in board.piece_map().items():
            piece = str(_piece)

            # piece values have more priority
            mg += ((Piece_Square_Tables.mg_values[piece.lower()] * (-1 if piece.islower() else 1))) / 100
            eg += ((Piece_Square_Tables.mg_values[piece.lower()] * (-1 if piece.islower() else 1))) / 100


            if piece.islower(): # black
                #if wq == False and piece.lower() == "k": # no restrictions if white queen of the table
                #    continue
                mg -= Piece_Square_Tables.PSQT_MG[piece][pos] / 100
                eg -= Piece_Square_Tables.PSQT_EG[piece][pos] / 100
            else:
                #if bq == False and piece.lower() == "k": # no restrictions if black queen of the table
                #    continue
                mg += Piece_Square_Tables.PSQT_MG[piece.lower()][Piece_Square_Tables.mirror_table[pos]] / 100
                eg += Piece_Square_Tables.PSQT_EG[piece.lower()][Piece_Square_Tables.mirror_table[pos]] / 100
            
            phase += Piece_Square_Tables.phase[piece.lower()]

        mobility = 0
        if not board.is_check():
            num_1 = board.legal_moves.count()
            board.push(chess.Move.null())
            num_2 = board.legal_moves.count()
            board.pop()
            if board.turn == chess.WHITE:
                mobility = num_1 - num_2
            else:
                mobility = num_2 - num_1

        mgp = min(phase, 24)
        egp = 24-mgp

        #evadj = 0

        '''
        if (len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2):
            evadj -= 500
        if (len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2):
            evadj += 500
        '''
        #sq = (mg * (256 - phase)) + ((eg * phase) / 256)
        sq = (mg * mgp + eg * egp) / 24 # idk about the legal moves

        white_pawns, black_pawns = [], []

        for k, v in pieces.items():
            if str(v) == 'P':
                white_pawns.append(k)
            elif str(v) == 'p':
                black_pawns.append(k)

        doubled_white = 0
        doubled_black = 0
        isolated_white = 0
        isolated_black = 0
        blocked_white = 0
        blocked_black = 0
        for pawn in white_pawns:
            # check for each pawn
            file_number = pawn % 8
            # is pawn blocked ( for white +8 for black -8)
            if pawn + 8 < 64 and board.piece_at(pawn + 8) is not None:
                blocked_white += 1
            has_left_neighbor = False
            has_right_neighbor = False
            if pawn % 8 == 0:
                has_left_neighbor = True
            if pawn % 8 == 7:
                has_right_neighbor = True
            # is it doubled, is another pawn on the file
            for other_pawn in white_pawns:
                if other_pawn != pawn and abs(pawn - other_pawn) % 8 == 0:
                    doubled_white += 1
                # isolation check left file ( if exists)
                other_file = other_pawn % 8
                if file_number - other_file == 1:
                    has_left_neighbor = True
                if file_number - other_file == -1:
                    has_right_neighbor = True
            if not has_left_neighbor and not has_right_neighbor:
                isolated_white += 1
        # check for black pawns
        for pawn in black_pawns:
            # check for each pawn
            file_number = pawn % 8
            # is pawn blocked ( for white +8 for black -8)
            if pawn - 8 >= 0 and board.piece_at(pawn - 8) is not None:
                blocked_black += 1
            has_left_neighbor = False
            has_right_neighbor = False
            if pawn % 8 == 0:
                has_left_neighbor = True
            if pawn % 8 == 7:
                has_right_neighbor = True
            # is it doubled, is another pawn on the file
            for other_pawn in black_pawns:
                if other_pawn != pawn and abs(pawn - other_pawn) % 8 == 0:
                    doubled_black += 1
                # isolation check left file ( if exists)
                other_file = other_pawn % 8
                if file_number - other_file == 1:
                    has_left_neighbor = True
                if file_number - other_file == -1:
                    has_right_neighbor = True
            if not has_left_neighbor and not has_right_neighbor:
                isolated_black += 1
        pawn_influence = ((doubled_white - doubled_black) + (isolated_white - isolated_black) + (blocked_white - blocked_black)) * 0.1
        #print(pawn_influence)
        sq -= pawn_influence

        return (sq + 0.1*mobility) * (-1 if board.turn == chess.BLACK else 1)

    # static exchange evaluation
    def static_exchange_evaluation(self, board, moveSquare):
        value = 0
        
        attackers = list(board.attackers(board.turn, moveSquare)) # get attackers to the square
        if attackers: # if we have attackers
            piece_types = [board.piece_type_at(x) for x in attackers] # get the piece type of these attackers
            lowest = min(piece_types, key=lambda x: Piece_Square_Tables.values[x]) # get lowest piece
            attacker_index = piece_types.index(lowest) # get index of lowest piece

            try:
                capture = Piece_Square_Tables.values[board.piece_type_at(moveSquare)] 
            except:
                capture = 100 # pawn
            
            try:
                next_move = board.find_move(attackers[attacker_index], moveSquare) # make capture move
                board.push(next_move) # push
                value = max(0, capture - self.static_exchange_evaluation(board, moveSquare))
                board.pop()
            except:
                value = 0
            
        return value

    # see capture
    def start_SEE(self, board, move): # push capture move
        value = 0
        m = move.to_square
        try:
            capture = Piece_Square_Tables.values[board.piece_type_at(m)]
        except:
            capture = 100 # pawn
        board.push(move)
        value = max(0, capture - self.static_exchange_evaluation(board, m))
        board.pop()
        return value

        
    # MOVE ORDERING
    def orderM(self, board, unscored_moves, pv_move, Quiscence):
        scored_moves = {}
        
        if Quiscence:
            for move in unscored_moves:

                if pv_move is not None and move == pv_move:
                    scored_moves[move] = 20000000
                    continue


                ## all non captures are at the end of the list
                if board.is_capture(move):
                    ## all captures have to be scored and thus sorted
                    #attacker = board.piece_at(move.from_square).symbol().lower()
                    #try:
                    #    victim = board.piece_at(move.to_square).symbol().lower()
                    #except:
                    #    victim = 'p'

                    #scored_moves[move] = self.Mvv_Lva_Scores[attacker][victim]
                    scored_moves[move] = self.start_SEE(board, move)
        else:
            for move in unscored_moves:
                ## all non captures are at the end of the list
                if not board.is_capture(move):

                    ### check if non capture is killer move 1st order
                    if self.killers[0][board.ply()] == move:
                        scored_moves[move] = 900000
                    elif self.killers[1][board.ply()] == move: # ????
                        scored_moves[move] = 800000
                    else:
                        scored_moves[move] = self.search_history[move.from_square][move.to_square]

                    # pawn promotions
                    if move.promotion:
                        scored_moves[move] += Piece_Square_Tables.values[move.promotion]
                else:
                    ## all captures have to be scored and thus sorted
                    #attacker = board.piece_at(move.from_square).symbol().lower()
                    #try:
                    #    victim = board.piece_at(move.to_square).symbol().lower()
                    #except:
                    #    victim = 'p'

                    #scored_moves[move] = self.Mvv_Lva_Scores[attacker][victim]
                    scored_moves[move] = self.start_SEE(board, move)

        ordered_move_list = sorted(scored_moves, key=scored_moves.get)
        ordered_move_list.reverse()
        return ordered_move_list

    @staticmethod
    def evaluate(board):
        return BOT.evaluate_EVAL(board)

    # QUISCENCE SEARCH
    def SearchAllCaptures(self, board, alpha, beta):

        old_a = alpha
        best_move = None
        h = board.fen()
        pv_move = self.get_pvline(h, board.turn)
        self.nodes += 1

        

        eval = self.evaluate(board) # change this (wtm = true for odd, false for even)
        if (eval >= beta):
            return beta
        
        # delta pruning
        
        if eval < alpha-9:
            return alpha
        
        alpha = max(alpha, eval)

        l = board.legal_moves

        captures = self.orderM(board, l, pv_move, True)
        #print(captures)
        
        for m in captures:

            board.push(m)
            eval = -self.SearchAllCaptures(board, -beta, -alpha) # this line slow asf
            board.pop()

            if eval > alpha:
                if eval >= beta:
                    return beta
                alpha = eval
                best_move = m


        if alpha != old_a:
            self.store_pvline(h, best_move)

        return alpha

    


    def startSearch(self, board):
        best_move_FOUND = None
        self.saved_moved = None
        self.clear_search_params()

        entry_time = time.time()


        for depth in range(1, settings.DEPTH):
            if time.time() - entry_time > settings.MAXT/(depth/4): # dont bother starting another depth if we ate through most our time
                print("TIMEOUT")
                break
            self.nodes = 0
            self.fh = 0
            self.fhf = 0
            currentItSearchDepth = depth + 1
            _start = time.time()

            best_score = self.search(board, depth, -BOT.INFINITY, BOT.INFINITY, depth, True)

            pvM = self.retrieve_pvline(board)
            if len(pvM) > 0:
                best_move_FOUND = pvM[0]
            else:
                if depth == settings.DEPTH-1:
                    best_score = self.search(board, depth+1, -BOT.INFINITY, BOT.INFINITY, depth+1, True)

                    print(f"XTRA: Depth {depth+1} Nodes: {self.nodes} Move: {board.san(best_move_FOUND)} Time: {time.time() - _start} Score: {best_score}")

            print(f"Depth {currentItSearchDepth} | Nodes: {self.nodes} | Move: {board.san(best_move_FOUND)} | Time: {time.time() - _start} | Score: {best_score}")
            print(f"Move Ordering {self.fhf /max(self.fh,1)}")
            print("PV LINE: ",self.get_pv_line_san(board, pvM))



            if best_score >= BOT.INFINITY - 100:
                # found checkmate
                return best_move_FOUND

        return best_move_FOUND


    def search(self, board, depth, alpha, beta, maxd, null_move):


        move_score = -BOT.INFINITY

        if board.is_checkmate():
            return board.ply() - BOT.INFINITY #* (-1 if board.turn else 1)
        elif board.is_stalemate() or board.is_repetition() or board.is_insufficient_material():
            return -(0 + BOT.contempt[self.getPhase(board)]) #* (-1 if board.turn else 1)
        

        # mate distance pruning ?
        if board.ply() > 0:
            alphaM = max(alpha, board.ply() - BOT.INFINITY)
            betaM = max (beta, BOT.INFINITY - board.ply())
            if alphaM >= betaM:
                return alphaM

        # transposition tables
        h = board.fen()

        hash_entry = self.get_hash(h)
        if hash_entry is not None:
            if hash_entry.depth >= depth:
                if hash_entry.flag == HashEntry.EXACT:
                    return hash_entry.score
                elif hash_entry.flag == HashEntry.ALPHA and hash_entry.score <= alpha:
                    return alpha
                elif hash_entry.flag == HashEntry.BETA and hash_entry.score >= beta:
                    return beta

        self.nodes += 1
        l = board.legal_moves

        # no legal moves 
        if l.count() == 0:
            return self.evaluate(board)
            
        razoringMargin = 5 # value of a queen (maybe change this)
        if depth <= 0:     
            return self.SearchAllCaptures(board, alpha, beta)
        elif depth <= 2: # razoring
            if alpha == beta - 1:
                if (self.evaluate(board) + razoringMargin * depth) < beta:
                    value = self.SearchAllCaptures(board, alpha, beta)
                    #move_score = -self.search(board, depth-2, -window[1], -window[0], maxd, null_move)
                    if value < beta:
                        return value
        #elif depth <= 4:
        #    if alpha == beta-1:
        #        if self.evaluate(board) < beta - (200 + 2 * depth):
        #            # razoring
        #            result = self.SearchAllCaptures(board, alpha, beta)
        #            if result < beta:
        #                return result


        if null_move and not board.is_check() and board.ply() > 0 and depth >= 3 and len(board.piece_map()) >= 10: #NULL MOVE - also wanna prevent zugzwang 
            board.push(chess.Move.null())
            move_score = -1 * self.search(board, depth - 3, -beta, -beta + 1, maxd, False)
            board.pop()

            if move_score >= beta:
                return beta

        move_score = -BOT.INFINITY
        best_score = -BOT.INFINITY

        old_a = alpha
        best_move = None
            
        moves = self.orderM(board, l, None, False)
        #print(moves)

        legal = 0
        pvM = self.retrieve_pvline(board)

        # implement PVS in the future

        # test first move



        for i, m in enumerate(moves):
            #m = Move.from_uci(m)
            if i == 0:
                board.push(m)
                move_score = -self.search(board, depth-1, -beta, -alpha, maxd, null_move)
            else:
                legal += 1

                wascheck = board.is_check()

                board.push(m)

                """                 
                elif depth <= 3:
                    
                    ev = self.evaluate(board)
                    if depth < 2:
                        value = ev + 2.5
                    elif depth < 3:
                        value = ev + 3.2
                    else:
                        value = ev + 4.7

                    if value < beta:
                        board.pop()
                        best_move = m
                        self.store_hash(board.fen(), best_move, beta, HashEntry.BETA, depth)
                        continue
                """
                # Aspiration window
                window = (alpha, alpha+1) if alpha+1 < beta else (alpha, beta)

                if i > 3 and depth > 3 and not board.is_check() and not board.is_capture(m) and m not in pvM and not wascheck: # LMR
                    move_score = -self.search(board, depth-2, -window[1], -window[0], maxd, null_move)
                else: move_score = -self.search(board, depth-1, -window[1], -window[0], maxd, null_move) # PVS
                
                # REDO PVS
                if (move_score > alpha and move_score > beta): # PVS
                    move_score = -self.search(board, depth-1, -beta, -alpha, maxd, null_move) # do full search
                    if move_score > alpha:
                        alpha = move_score
                    
            
            board.pop()
            if move_score > best_score:
                best_score = move_score
                best_move = m

                if move_score > alpha:
                    if move_score >= beta:
                        if legal == 1:
                            self.fhf += 1
                        self.fh += 1
                        # killer moves
                        if not board.is_capture(m):
                            self.killers[1][board.ply()] = self.killers[0][board.ply()]
                            self.killers[0][board.ply()] = m

                        self.store_hash(board.fen(), best_move, beta, HashEntry.BETA, depth)
                        return beta

                    alpha = move_score
                    best_move = m
                    if not board.is_capture(m):
                        self.search_history[best_move.from_square][best_move.to_square] += depth



        if alpha != old_a:

            self.store_hash(board.fen(), best_move, best_score, HashEntry.EXACT, depth)
        else:

            # STORE HASH pos, bestmove, alpha, ALPHA, depth
            self.store_hash(board.fen(), best_move, alpha, HashEntry.ALPHA, depth)



        return alpha


    ############################ BOT/MODULE INTERFACE #################################



    def tablebase(self, board) :
        if len(board.piece_map()) <= 7 :
            try :
                fen = board.fen().replace(' ', '_')
                info = requests.get(f'http://tablebase.lichess.ovh/standard?fen={fen}')
                return info.json()['moves'][0]['uci']
            except Exception :
                pass
        return None

    def play(self, board): # 

        r = self.get_opening_move(board)
        if r is not None:
            return r
        

        r = self.tablebase(board)
        if r == None:
            r = self.startSearch(board)
        return r


# testing
if __name__ == "__main__":
    #board = chess.Board("1k1r4/pp1b1R2/3q2pp/4p3/2B5/4Q3/PPP2B2/2K5 b - - 0 1")
    board = chess.Board("r1b2r1k/2qnb1pp/p2pNn2/1p6/4P3/P1N1B1Q1/1PP2PPP/R4R1K b - - 0 16")
    #board = chess.Board("8/8/8/1K6/1p1kPb2/1Pp5/P1B5/8 b - - 6 64")
    #board = chess.Board("8/7K/8/8/8/8/R7/7k w - - 0 1")
    #print(list(board.pieces))
    board.turn = False
    pr = cProfile.Profile()
    pr.enable()
    print(BOT().play(board))
    pr.disable()
    ps = pstats.Stats(pr).sort_stats('tottime')
    ps.print_stats()
