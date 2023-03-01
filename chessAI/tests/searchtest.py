import chessUtil
import cProfile
import pstats


fen = "1k1r4/pp1b1R2/3q2pp/4p3/2B5/4Q3/PPP2B2/2K5 b - - 0 1"
game = chessUtil.GameState()



def test(depth):
    if depth == 0:
        return 1
    moves = game.getAllPossibleMoves()
    numpos = 0

    for m in moves:
        game.makeMove(m)
        numpos += test(depth-1)
        game.undoMove()

    return numpos



pr = cProfile.Profile()
pr.enable()

for i in range(1, 6):
    print(f"Depth {i} Result: {test(i)} positions")

pr.disable()
ps = pstats.Stats(pr).sort_stats('tottime')
ps.print_stats()