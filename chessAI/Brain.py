'''
Yangbot #1 - elo ~ 1500+ 
* lost to wally (1800) - accuracy unknown
* lost to stockfish 5 (1700)
* lost to Isabel (1600)
* Drew to Antonio (1500)
* Won against Nelson (1300)

'''

import chess
from chess import Move
import chess.engine
import chess.polyglot
from random import choice
from math import inf
import numpy as np
import cProfile
import pstats
from multiprocessing import Pool
from functools import partial
#from collections import Counter




class BOT():

    def __init__(self):
        #self.engine = chess.engine.SimpleEngine.popen_uci(r"C:\\Users\\clare\\Downloads\\stockfish_15.1_win_x64_avx2\\stockfish_15.1_win_x64_avx2\\stockfish-windows-2022-x86-64-avx2.exe")


        self.values = [100, 320, 330, 500, 1000]
        self.phase = [0, 1, 1, 2, 4]
        self.total = self.phase[0] * 16 + self.phase[1] * 4 + self.phase[2] * 4 + self.phase[3] * 4 + self.phase[4] * 2

        self.bestmove = None
        self.bestmovethisit = None
        self.besteval = 0
        self.bestevalthisit = 0
        self.abort = False
        self.currentItSearchDepth = 0

        #self.bookMoves = 5
        self.hash = {}



        self.pawns = [
            0,   0,   0,   0,   0,   0,  0,   0,
            98, 134,  61,  95,  68, 126, 34, -11,
            -6,   7,  26,  31,  65,  56, 25, -20,
            -14,  13,   6,  21,  23,  12, 17, -23,
            -27,  -2,  -5,  12,  17,   6, 10, -25,
            -26,  -4,  -4, -10,   3,   3, 33, -12,
            -35,  -1, -20, -23, -15,  24, 38, -22,
            0,   0,   0,   0,   0,   0,  0,   0
        ]

        self.knights = [
            -167, -89, -34, -49,  61, -97, -15, -107,
            -73, -41,  72,  36,  23,  62,   7,  -17,
            -47,  60,  37,  65,  84, 129,  73,   44,
            -9,  17,  19,  53,  37,  69,  18,   22,
            -13,   4,  16,  13,  28,  19,  21,   -8,
            -23,  -9,  12,  10,  19,  17,  25,  -16,
            -29, -53, -12,  -3,  -1,  18, -14,  -19,
            -105, -21, -58, -33, -17, -28, -19,  -23
        ]

        self.bishop = [
            -29,   4, -82, -37, -25, -42,   7,  -8,
            -26,  16, -18, -13,  30,  59,  18, -47,
            -16,  37,  43,  40,  35,  50,  37,  -2,
            -4,   5,  19,  50,  37,  37,   7,  -2,
            -6,  13,  13,  26,  34,  12,  10,   4,
            0,  15,  15,  15,  14,  27,  18,  10,
            4,  15,  16,   0,   7,  21,  33,   1,
            -33,  -3, -14, -21, -13, -12, -39, -21
        ]

        self.rooks = [
            32,  42,  32,  51, 63,  9,  31,  43,
            27,  32,  58,  62, 80, 67,  26,  44,
            -5,  19,  26,  36, 17, 45,  61,  16,
            -24, -11,   7,  26, 24, 35,  -8, -20,
            -36, -26, -12,  -1,  9, -7,   6, -23,
            -45, -25, -16, -17,  3,  0,  -5, -33,
            -44, -16, -20,  -9, -1, 11,  -6, -71,
            -19, -13,   1,  17, 16,  7, -37, -26
        ]

        self.queens = [
            -28,   0,  29,  12,  59,  44,  43,  45,
            -24, -39,  -5,   1, -16,  57,  28,  54,
            -13, -17,   7,   8,  29,  56,  47,  57,
            -27, -27, -16, -16,  -1,  17,  -2,   1,
            -9, -26,  -9, -10,  -2,  -4,   3,  -3,
            -14,   2, -11,  -2,  -5,   2,  14,   5,
            -35,  -8,  11,   2,   8,  15,  -3,   1,
            -1, -18,  -9,  10, -15, -25, -31, -50
        ]

        self.kingMiddle = [
            -65,  23,  16, -15, -56, -34,   2,  13,
            29,  -1, -20,  -7,  -8,  -4, -38, -29,
            -9,  24,   2, -16, -20,   6,  22, -22,
            -17, -20, -12, -27, -30, -25, -14, -36,
            -49,  -1, -27, -39, -46, -44, -33, -51,
            -14, -14, -22, -46, -44, -30, -15, -27,
            1,   7,  -8, -64, -43, -16,   9,   8,
            -15,  36,  12, -54,   8, -28,  24,  14
        ]

        self.kingEnd = [
            -50,-40,-30,-20,-20,-30,-40,-50,
            -30,-20,-10,  0,  0,-10,-20,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-30,  0,  0,  0,  0,-30,-30,
            -50,-30,-30,-30,-30,-30,-30,-50
        ]



    def evaluate(self, board):

        if board.is_checkmate():
            if board.turn:
                return -9999
            return 9999

        if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition():
            return 0

        phase = self.total
        white, black = 0, 0
        
        
        
        white = len(board.pieces(1, True)) * 100 + len(board.pieces(2, True)) * 300 + len(board.pieces(3, True)) * 300 + len(board.pieces(4, True)) * 500 + len(board.pieces(5, True)) * 900
        black = len(board.pieces(1, False)) * 100 + len(board.pieces(2, False)) * 300 + len(board.pieces(3, False)) * 300 + len(board.pieces(4, False)) * 500 + len(board.pieces(5, False)) * 900

        
        #b = Counter(str(board))
        '''
        b.count('P') * 100 + b.count('N') * 300 + b.count('B') * 300 + b.count('R') * 500 + b.count('Q') * 900
        '''
        

        #white = b['P'] * 100 + b['N'] * 300 + b['B'] * 300 + b['R'] * 500 + b['Q'] * 900
        #black = b['p'] * 100 + b['n'] * 300 + b['b'] * 300 + b['r'] * 500 + b['q'] * 900

        
        sq = sum([sum([self.pawns[chess.square_mirror(i)] for i in board.pieces(1, True)]) - sum([self.pawns[i] for i in board.pieces(1, False)]), 
        sum([self.knights[chess.square_mirror(i)] for i in board.pieces(2, True)]) - sum([self.knights[i] for i in board.pieces(2, False)]), 
        sum([self.bishop[chess.square_mirror(i)] for i in board.pieces(3, True)]) - sum([self.bishop[i] for i in board.pieces(3, False)]), 
        sum([self.rooks[chess.square_mirror(i)] for i in board.pieces(4, True)]) - sum([self.rooks[i] for i in board.pieces(4, False)]), 
        sum([self.queens[chess.square_mirror(i)] for i in board.pieces(5, True)]) - sum([self.queens[i] for i in board.pieces(5, False)]),
        sum([self.kingMiddle[chess.square_mirror(i)] for i in board.pieces(6, True)]) - sum([self.kingMiddle[i] for i in board.pieces(6, False)])]) 

        
        
        #kM = sum([self.kingMiddle[chess.square_mirror(i)] for i in board.pieces(6, True)]) - sum([self.kingMiddle[i] for i in board.pieces(6, False)])
        #kE = sum([self.kingEnd[chess.square_mirror(i)] for i in board.pieces(6, True)]) - sum([self.kingEnd[i] for i in board.pieces(6, False)])

        #sq += (kM * (256 - phase)) + (kE * phase / 256)


        '''
        sq = 0
        
        pieces = {1: self.pawns, 2: self.knights, 3: self.bishop, 4: self.rooks, 5: self.queens, 6: self.kingMiddle}
        for pt, square in pieces.items():
            for s in board.pieces(pt, True):
                sq += square[s]
            for s in board.pieces(pt, False):
                sq -= square[chess.square_mirror(s)]
        '''

        eval = (white-black) + sq
        #wmwop = white - str(board.pieces(1, True)).count('1')
        #bmwop = black - str(board.pieces(1, False)).count('1')

        #whiteEndgame = self.endGameW(wmwop)
        #blackEndgame = self.endGameW(bmwop)

        #whiteEval += white
        #blackEval += black

        #whiteEval += self.evalPST(board, True, whiteEndgame)
        #blackEval += self.evalPST(board, False, blackEndgame)

        

        if board.turn:
            return eval 
        return -eval
        


    def SearchAllCaptures(self, board, alpha, beta, legal):
        eval = self.evaluate(board) # change this (wtm = true for odd, false for even)
        if (eval >= beta):
            return beta
        
        alpha = max(alpha, eval)

        captures = self.orderMoves(board, legal, True)
        
        
        for m in captures:
            #m = Move.from_uci(m)
            board.push(m)
            eval = -self.SearchAllCaptures(board, -beta, -alpha, board.legal_moves) # this line slow asf
            board.pop()

            if eval >= beta:
                return beta
            
            
            alpha = max(alpha, eval)

        return alpha


    def getMoveGuess(self, board, m, c):
        if not board.is_capture(m) and c: # skip for non capture
            return None

        btm = board.turn
        movescoreguess, move = 0, m
        start, end = move.from_square, move.to_square
        movePieceType, endPieceType = board.piece_type_at(start), board.piece_type_at(end)



        if str(m) == 'O-O' or str(m) == 'O-O-O': # good idea to castle if haven't already
            movescoreguess += 10

        if movePieceType != 6:
            #print(movePieceType)
            if board.is_attacked_by(not btm, start): # probably good idea to move attacked piece
                movescoreguess += self.values[movePieceType-1]
            
            if endPieceType != None: # captures
                movescoreguess = 10 * self.values[endPieceType-1] - self.values[movePieceType-1]
            a = [board.piece_type_at(e) for e in board.attackers(not btm, end)]
            if a: # bad idea to move to attacked square
                if 1 in a:
                    movescoreguess -= 350
                else:
                    movescoreguess -= self.values[movePieceType-1]
            else:
                if movePieceType == 1:
                    movescoreguess += 100 # free pawn to push

        if movePieceType == 4 and endPieceType == None: # try not to move rook randomly
            movescoreguess -= 10

        if move.promotion != None:
            movescoreguess += self.values[move.promotion-1]
        

        return movescoreguess

    def orderMoves(self, board, lists, capturesOnly):
        #result = []

        #moves = np.array(list(lists))
        #results = (x for x, s in list if self.getMoveGuess(board, x, capturesOnly))
        #scores = np.array([self.getMoveGuess(board, move, capturesOnly) for move in moves])
        #mask = scores != None

        
        #ind = np.argsort(scores[mask])
        #return np.array(moves[mask])[ind]

        v = [(move, score) for move, score in ((move, self.getMoveGuess(board, move, capturesOnly)) for move in lists) if score is not None] 
        #print(v)
        
        #print(result)
        return [move for move, _ in sorted(v, key=lambda x: x[1], reverse=True)]
        #return [y for m, y in sorted(result, reverse=True)]
        #moves = np.array(moves)
        #scores = np.array(scores)
        #print(moves)
        #inds = scores.argsort()

        #return moves[inds[::-1]]



    def startSearch(self, board):
        self.bestevalthisit, self.besteval = 0, 0
        self.bestmovethisit, self.bestmove = None, None

        self.hash.clear() # ???

        self.currentItSearchDepth = 0
        self.abort = False

        targetD = 4

        for i in range(1, targetD):
            self.search(board, i, 0, -inf, inf)

            if self.abort:
                break
            else:
                self.currentItSearchDepth = i
                self.bestmove = self.bestmovethisit
                self.besteval = self.bestevalthisit
        
        
        return self.bestmove


    def lookUpTT(self, board, depth, plyfromroot, alpha, beta):
        s = chess.polyglot.zobrist_hash(board)
        if s in self.hash:
            if self.hash[s][1] >= depth: # key: board, values: eval, depth, nodetype, move
                score = self.hash[s][0]
                move = self.hash[s][3]

                if self.hash[s][2] == 0:
                    return score, move

                if self.hash[s][2] == 2 and score <= alpha:
                    return score, move

                if self.hash[s][2] == 1 and score >= beta:
                    return score, move

        return None, None

    
    def storeTT(self, board, depth, numPly, eval, evalType, move):
        s = chess.polyglot.zobrist_hash(board)
        self.hash[s] = (eval, depth, evalType, move)

    def search(self, board, depth, plyfromroot, alpha, beta):

        if self.abort:
            return 0

        if plyfromroot > 0:
            alpha = max(alpha, -100000 + plyfromroot)
            beta = min(beta, 100000 - plyfromroot)
            if alpha >= beta:
                return alpha


        ttval = self.lookUpTT(board, depth, plyfromroot, alpha, beta)
        if ttval[0] != None:
            if plyfromroot == 0:
                self.bestmovethisit = ttval[1]
                self.bestevalthisit = ttval[0]

            return ttval[0]

        l = board.legal_moves

        if depth == 0:
            result = self.SearchAllCaptures(board, alpha, beta, l)
            #self.hash[s] = result
            return result
            #return(self.evaluate(board, False), None)

        

            
        moves = self.orderMoves(board, set(l), False)

        if len(list(moves)) == 0:
            if board.is_check():
                #self.hash[s] = (-inf, None)
                return -(100000 - plyfromroot)
            return 0

        #bestE = -math.inf
        evalType = 2
        bestMove = None
        #bestMoveThisPos = list(board.legal_moves)[0]
        #eval = 0

        for m in moves:
            #m = Move.from_uci(m)
            board.push(m)
            eval = -self.search(board, depth-1, plyfromroot + 1, -beta, -alpha)
            board.pop()
            if eval >= beta:
                self.storeTT(board, depth, plyfromroot, beta, 1, m)
                return beta
            #bestE = max(eval, bestE)
            if eval > alpha:
                evalType = 0
                alpha = eval
                bestMove = m
                if plyfromroot == 0:
                    self.bestmovethisit = m
                    self.bestevalthisit = eval
                #bestE = eval
                #return alpha
                #print(bestMove)
            



        self.storeTT(board, depth, plyfromroot, alpha, evalType, bestMove)

        return alpha


    def play(self, board): # 
        try:
            return chess.polyglot.MemoryMappedReader("chessAI/data/polyglot/performance.bin").weighted_choice(board).move
        except:
            return self.startSearch(board)

        

if __name__ == "__main__":
    board = chess.Board("r1b2r1k/2qnbppp/p2pBn2/1p6/3NP3/P1N1B1Q1/1PP2PPP/R4R1K b - - 0 15")
    #print(list(board.pieces))
    board.turn = False
    pr = cProfile.Profile()
    pr.enable()
    print(BOT().play(board))
    pr.disable()
    ps = pstats.Stats(pr).sort_stats('tottime')
    ps.print_stats()

#bot.orderMoves(board)
#print(bot.play(board))
#print(bot.moveGen(4, board))
#print(bot.eval(board, True))