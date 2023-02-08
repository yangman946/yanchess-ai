'''
FEATURE LIST:
- UCI interface
- negamax
- quiscence search
- move ordering
- PST 
- evaluation 
    > PeSTO evaluation
    > Incremental material counting
- iterative deepening
- null moves
- late move reduction
- transposition tables
- principal variation search
- mate distance pruning
- razoring
- check extensions


BOTS:
- https://github.com/tuxmania87/chessbot-tuxbot
- https://github.com/thomasahle/sunfish/blob/master/sunfish.py 
- https://github.com/eligolf/Affinity-Chess 


OTHER benchmarking:
- Perft function
- bulk counting 

'''

from utils import ai

version = "Yangbot 1.0.0"
Author = "Clarence Yang"

bot = None

# UCI interface
print("You are playing with Yangbot!")

while True:
    args = input().split()

    if args[0] == "uci":
        print(f"id name {version}")
        print(f"id author {Author}")
    elif args[0] == "quit":
        break
    elif args[0] == "isready":
        print("readyok")
    elif args[0] == "position":
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        ind = 2
        moves = []
        if args[1] == "fen":
            fen = args[2] + args[3] + args[4] + args[5] + args[6] + args[7]
            ind = 8

        if "moves" in args:
            moves = args[ind+1:]

        bot = ai.ai(fen, moves)
        
    elif args[0] == "go":
        if bot != None:
            result = bot.startSearch()
            print(f"bestmove {result}")
            #for i in range(1, 5):
            #    print(f"Depth {i} results: {bot.moveGenTest(i)}")
        pass
    