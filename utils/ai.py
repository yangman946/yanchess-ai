import chess
from utils import search


class ai:

    def __init__(self, fen, moves):
        self.board = chess.Board(fen)
        self.nodes = 0
        self.depth = 5
        self.search = search.search()

        for m in moves:
            self.board.push_uci(m)

    def moveGenTest(self, depth):
        if depth == 0:
            return 1
        moves = self.board.legal_moves
        pos = 0

        for m in moves:
            self.board.push(m)
            pos += self.moveGenTest(depth-1)
            self.board.pop()
        
        return pos

    def startSearch(self):
        moves = self.board.legal_moves
        currentDepth = 0
        besteval = -9999
        bestMove = chess.Move.null()

        for i in range(1, self.depth):
            for m in moves:
                self.board.push(m)
                score = 
                self.board.pop()
        
        pass

    
        

