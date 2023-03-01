'''
Todo:
- add takebacks 
- create theme settings
- create game settings (timer)
- choose bots
- fix bug with seeking


'''

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import customtkinter
from PIL import Image, ImageTk
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from multiprocessing import Pool
import queue
import threading

import random

import chess
import chess.engine
#from playsound import playsound
from pygame import mixer
import AI
import Brain
import test



class chess_GUI():

    def __init__(self):

        self.WIDTH = 600
        self.HEIGHT = 600
        self.offset = 300
        self.BLOCKX = self.WIDTH/8
        self.BLOCKY = self.HEIGHT/8

        # load some user prefs

        self.playingbot = True
        self.botIndex = 1
        self.YANGBOTMAX = r"D:\C# projects\CHESSBOT\Chess_yangbotMax\Chess_yangbotMax\bin\Debug\net6.0\Chess_yangbotMax.exe"

        self.player = 0 # white to move (1 is black)
        self.playerid = 0 # only matters when playing bot | choose black or white (or random)
        self.moves = [] # click --> click

        self.previousmove = []

        self.img = []
        self.floating = None
        self.movedout = False
        self.phase = 0

        self.checked = []

        self.piecesW = {'1': '♙', '2': '♘', '3': '♗', '4': '♖', '5': '♕'}
        self.piecesB = {'1': '♟', '2': '♞', '3': '♝', '4': '♜', '5': '♛'}

        self.wCaptures = ''
        self.bCaptures = ''

        self.values = [1, 3, 3, 5, 9]

        self.q = queue.Queue()
        
        mixer.init()
        
        #which bot is superior?

        #self.bot = Brain.BOT()
        #self.bot = AI.BOT()

        customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
        customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

        # icon not changing?
        self.master = customtkinter.CTk()
        self.master.resizable(False, False)
        self.master.title("Chess")
        self.master.iconbitmap(f"{os.getcwd()}\\assets\\wP.ico")

        f = customtkinter.CTkFrame(self.master, height = self.HEIGHT + 50, bg_color='transparent')
        f2 = customtkinter.CTkFrame(self.master, height= self.HEIGHT + 50, width=self.offset, corner_radius=20, fg_color='transparent')
        
        
        self.master.geometry(f"{self.WIDTH + self.offset + 150}x{self.HEIGHT + 115}")
        self.w = Canvas(f, width=self.WIDTH, height=self.HEIGHT)
        
        f.grid(row=0, column=0, padx=50, pady=50)
        #f.pack(fill=BOTH, expand=True)
        f2.grid(row=0, column=1,padx=(0,20), pady=(0,20))
        
        self.bot = None
        if self.playingbot:
            if self.botIndex == 0:
                self.bot = Brain.BOT()
            elif self.botIndex == 1:
                self.bot = AI.BOT()
                #self.bot = test.MovementGenerator()
            elif self.botIndex == 3:
                self.bot = test.BOT()
            elif self.botIndex == 2:
                self.bot = chess.engine.SimpleEngine.popen_uci(self.YANGBOTMAX)


        self.board = chess.Board() #"6rk/pp1rpp1p/2qp1n1Q/7P/4P3/2N2P2/PPP5/1K1R2R1 w - - 3 22"
        print(self.board)
        self.starting = self.board.fen()

        self.seekind = 0
        self.moveHistory = [(self.board.fen(), [], None)] # (fen, move)
        self.seeking = False
        self.gameover = False

        tabview = customtkinter.CTkTabview(f2, height=self.HEIGHT+25, width=self.offset, corner_radius=20)
        tabview.add("Game")  # add tab at the end
        tabview.add("Settings")  # add tab at the end
        tabview.set("Game")
        tabview.pack()

        f3 = customtkinter.CTkFrame(tabview.tab("Game"), height = 20, width = self.offset-30)
        f3.place(relx=0.5, rely=0.7, anchor=CENTER)
        my_font = customtkinter.CTkFont(family="Century Gothic", size=30)
        self.my_font2 = customtkinter.CTkFont(family="Century Gothic", size=20)
        my_font3 = customtkinter.CTkFont(family="Segoe UI Symbol", size=30)
        my_font4 = customtkinter.CTkFont(family="Century Gothic", size=15)
        title = customtkinter.CTkLabel(master=tabview.tab("Game"), text="YanChess", font=my_font)
        title.place(relx=0.5, rely=0.075, anchor=CENTER)
        self.status = customtkinter.CTkLabel(master=tabview.tab("Game"), text="White to move", font=my_font4)
        self.status.place(relx=0.5, rely=0.3, anchor=CENTER)
        self.captures1 = customtkinter.CTkLabel(master=self.master, text="", font=my_font3)
        self.captures1.place(relx=0.06, rely=0.04, anchor=W)
        self.captures2 = customtkinter.CTkLabel(master=self.master, text="", font=my_font3)
        self.captures2.place(relx=0.06, rely=0.95, anchor=W)

        first = customtkinter.CTkButton(master=f3,
                    text="<<",
                    width=20,
                    command=lambda: self.seek(0)).grid(row=0, column=0, padx=10)
        next = customtkinter.CTkButton(master=f3,
                    text=">",
                    width=20,
                    command=lambda: self.seek(self.seekind+1)).grid(row=0, column=2, padx=10)
        prev = customtkinter.CTkButton(master=f3,
                    text="<",
                    width=20,
                    command=lambda: self.seek(self.seekind-1)).grid(row=0, column=1, padx=10)
        last = customtkinter.CTkButton(master=f3,
                    text=">>",
                    width=20,
                    command=lambda: self.seek(len(self.moveHistory)-1)).grid(row=0, column=3, padx=10)
        #next.place(relx=0.5, rely=0.925, anchor=CENTER)
        

        button = customtkinter.CTkButton(master=tabview.tab("Game"),
                                 width=150,
                                 height=40,
                                 border_width=0,
                                 corner_radius=8,
                                 text="New Game",
                                 font=self.my_font2,
                                 command=lambda: self.newgame())
        button.place(relx=0.5, rely=0.925, anchor=CENTER)
        

        #movelistlabel = customtkinter.CTkLabel(master=f2, text="hello")
        #movelistlabel.place(relx=0.5, rely=0.15, anchor=CENTER)

        self.MovesList = customtkinter.CTkTextbox(tabview.tab("Game"), height=150, width=260, corner_radius=8, border_width=2)
        self.MovesList.configure(state=DISABLED)
        self.MovesList.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        switch_1 = customtkinter.CTkSwitch(master=tabview.tab("Settings"), text="Play bot?", command=None,
                                   variable=None, onvalue="on", offvalue="off")

        switch_1.place(relx=0.5, rely=0.3, anchor=CENTER)

        self.createBoard(str(self.board.fen()), self.previousmove, self.isflip())
        self.p = None
        

        self.master.bind('<Motion>', self.callback) # click
        self.master.bind('<ButtonPress-1>', self.callbackHold)
        self.master.bind('<ButtonRelease-1>', self.callbackRelease)
        self.master.protocol('WM_DELETE_WINDOW', self.onclose)

        

        self.master.mainloop()

        
        #config = board.STARTING_FEN





    def onclose(self):
        #sys.exit()
        self.master.quit()
        #self.master.destroy()
        quit()

    def newgame(self):
        '''
        pr = customtkinter.CTkToplevel(self.master)
                
        pr.title("New Game")
        pr.geometry("300x300")
        pr.resizable(False, False)

        l = customtkinter.CTkLabel(pr, text="New Game", font=self.my_font2)
        l.pack(side="top", padx=40, pady=20)

        choice = IntVar()

        aiops = ["Yangbot A", "Yangbot B"]
        time = []
        ai = StringVar()
        ai.set(aiops[0])
        #style = ttk.Style()
        #style.configure('W.TButton', borderwidth=0)


        tabview = customtkinter.CTkTabview(pr, height=200, width=250, corner_radius=10)
        tabview.add("Player")  # add tab at the end
        tabview.add("AI")  # add tab at the end
        tabview.set("Player")
        tabview.pack()


        combobox = customtkinter.CTkOptionMenu(tabview.tab("AI"), ai, aiops)
        combobox.pack(padx=20, pady=10)

        btn3 = customtkinter.CTkButton(tabview.tab("Player"), text="Confirm", command=lambda: choice.set(1))
        btn3.pack(side="bottom", padx=40, pady=10)
        

        btn4 = customtkinter.CTkButton(tabview.tab("AI"), text="Confirm", command=lambda: choice.set(2))
        btn4.pack(side="bottom", padx=40, pady=10)

        pr.wait_variable(choice)
        print(ai.get())

        pr.destroy()

        '''
        if self.board.fen() == self.starting:
            return
        answer = messagebox.askyesno(title='confirmation',
                    message='Are you sure that you want to start a new game?')
        if not answer:
            return
        self.previousmove = []

        self.player = 0 # white to move (1 is black)

        self.bCaptures = ''
        self.wCaptures = ''
        self.captures2.configure(text='') 
        self.captures1.configure(text='') 
        self.gameover = False
        self.status.configure(text='White to move') 

        self.floating = None
        self.MovesList.configure(state="normal")
        self.MovesList.delete('1.0', END)
        self.MovesList.configure(state="disabled")

        self.moveHistory = []
        self.seekind = 0
        self.checked = []
        self.seeking = False
        self.board.reset()
        self.reset()
        
    

    def playsounds(self, sound):
        chnl = mixer.Channel(self.player)
        v = mixer.Sound(f'{os.getcwd()}\\sounds\\{sound}.mp3')
        chnl.play(v)


    def callbackHold(self, e):
        #print("HOLDING")
        #print(f"{e.x},{e.y} - {str(e.widget)}")
        

        if (str(e.widget) != ".!ctkframe.!canvas"):
            return
        
        if self.seeking:
            return

        if self.playingbot and self.player != self.playerid:
            return


        # get mouse pos and convert to the square
        x= int(e.x/self.WIDTH * 8)
        y= int(e.y/self.HEIGHT * 8)
        #print(f"{x},{y}")

        if self.isflip():
            #x = 7-x
            #y = 7-y
            pos = f"{chr((7-x)+97)}{y+1}"
            p = self.findPiece(7-x,7-y,self.board.fen()) # check if there is a piece there
        else:
            pos = f"{chr(x+97)}{8-y}" # square in chess notation
            p = self.findPiece(x,y,self.board.fen()) # check if there is a piece there
        #print(f"Pointer is currently at {pos}")
        

        on_piece = False

        if p == "none": #ignore if we hit an empty space
            if self.phase == 1: # dont ignore if we are choosing a space to move
                self.moves.append(pos) # add to moves
                return
            self.reset()
            return
        else:
            
            #print(f"Pointer currently over {p}: {pos}")
            
            # can only drag if mouse is over one of our pieces
            if (self.player == 0 and "w" in p) or (self.player == 1 and "b" in p):
                on_piece = True
                if self.phase == 1 and pos not in self.moves: # if we clicked on of our own pieces after already selected one
                    self.reset()
                self.floating = PhotoImage(file = f"{os.getcwd()}\\images\\{p}.png")
                #piece = Label(master=self.master, image=self.floating)
                
                self.w.create_image(e.x, e.y, image=self.floating, anchor="center", tag="piece")
                #e.widget.tag_upper(e.widget.find_withtag('piece'))

            self.moves.append(pos) # add to moves



        #print(self.moves)

        


        if on_piece: # first time hitting a piece
            
            self.drawlegalMoves(True, self.isflip()) # draw the legal moves
 
        self.phase += 1 # increase counter 

    def callback(self, e): # motion
        if self.seeking:
            return

        if self.playingbot and self.player != self.playerid:
            return

        if (self.floating != None): # only active if we move a piece
            self.w.coords("piece", e.x, e.y)
            self.w.tag_raise("piece")

            x= int(e.x/self.WIDTH * 8)
            y= int(e.y/self.HEIGHT * 8)
            #if self.isflip():
            #    x = 7-x
            #    y = y
            if self.isflip():
                #x = 7-x
                #y = 7-y
                pos = f"{chr((7-x)+97)}{y+1}"
            else:
                pos = f"{chr(x+97)}{8-y}" # square in chess notation

            if pos != self.moves[0]:
                self.movedout = True
            
        pass

    def callbackRelease(self, e): # released
        #print("RELEASED")
        # de-select piece
        if self.seeking:
            return

        if self.playingbot and self.player != self.playerid:
            return 

        self.floating = None 
        self.w.delete("piece")

        # get mouse pos and convert to the square
        x= int(e.x/self.WIDTH * 8)
        y= int(e.y/self.HEIGHT * 8)
        #if self.isflip():
        #    x = 7-x
        #    y = y

        if self.isflip():
            #x = 7-x
            #y = 7-y
            pos = f"{chr((7-x)+97)}{y+1}"
            p = self.findPiece(7-x, 7-y, self.board.fen())
        else:
            pos = f"{chr(x+97)}{8-y}" # square in chess notation
            p = self.findPiece(x, y, self.board.fen())

        

        if len(self.moves) == 0:
            return

        
        if (self.player == 0 and "w" in p) or (self.player == 1 and "b" in p):
            self.drawlegalMoves(False, self.isflip())
        if pos == self.moves[0]: # if our piece hadn't moved
            if self.movedout: # if we dragged our piece randomly
                self.reset()
                return
            
        else:
                
            self.moves.append(pos)
            self.movePiece()

        #print(self.moves)

        if self.phase > 1:
            self.reset()

    def reset(self, nextplayer = False):
        self.movedout = False
        self.moves = []
        self.img = None
        self.phase = 0

        

        if nextplayer:
            player = "White"
            self.player += 1
            text = "Black to move"
            if self.player > 1:
                player = "Black"
                text = "White to move"
                self.player = 0

            self.createBoard(self.board.fen(), self.previousmove, self.isflip())
            self.master.update()
        
            if self.board.is_checkmate():
                text = f"Checkmate by {player}!"
                self.gameover = True
            elif self.board.is_stalemate():
                text = f"Stalemate!"
                self.gameover = True
            elif self.board.is_repetition():
                text = f"Draw by repetition!"
                self.gameover = True
            elif self.playingbot == True and self.player != self.playerid:
                # bot turn to move
                
                #x = threading.Thread(target=self.botMove)
                #x.start()
                #self.master.after(1000, self.botMove)
                text = "Opponent is thinking..."
                self.status.configure(text=text) 
                self.botMove()
                return
                

            if self.gameover == True: self.playsounds('gameover')
            self.status.configure(text=text) 
        else:
            self.createBoard(self.board.fen(), self.previousmove, self.isflip())
            self.master.update()
            
            


                

 
                

    def botMove(self):
        
        if self.botIndex == 2:
            r = self.bot.play(self.board, chess.engine.Limit(time=1))
            r = r.move
        else:
            with Pool() as pool:
                r = pool.apply_async(self.bot.play, (self.board,))
                while not r.ready():
                    self.master.update()


                r = r.get()

        
        print(r)
        if r == None:
            r = random.choice(list(self.board.legal_moves)) # random move - usually happens when we are close to being checkmated
            action = chess.Move.from_uci(str(r))
            print("good game!")
        else:
            #print(r)
            action = chess.Move.from_uci(str(r))

        self.move(str(r), action)


    def move(self, r, action):


        promote = ['q', 'r', 'b','n']
        standard = self.board.san(action)
        

        if r[-1] in promote:
            r = r[:-1]

        first_half  = r[:len(r)//2]
        second_half = r[len(r)//2:]

        moves = [first_half, second_half]
        
        sound = ""
        iscapture = False
        isE = False

        if self.board.is_en_passant(action):
            isE = True
            sound = "capture"
        elif self.board.is_capture(action):
            iscapture = True
            sound = "capture"
        else:
            sound = "move-self"

        self.playsounds(sound)
        


        self.moveHistory.append((self.board.fen(), moves, standard))
        self.seekind = len(self.moveHistory)-1

        #self.seek(len(self.moveHistory)-1)

        #print(standard)

        self.updateMoveslist(self.seekind, True, iscapture, isE)
        self.board.push(action)
        self.previousmove = moves

        if self.board.is_check():
            self.checked = []
            self.checked.append(self.player)
            sound = "move-check"


        #y = threading.Thread(target=self.playsounds, args=(sound,))
        #y.daemon = True
        #y.start()
        
        self.reset(nextplayer=True)
    
                

    def isflip(self):

        # make another check for if player plays black against ai?

        flip = (self.playingbot == False and self.player == 1)
        #print("Flipped: " + str(flip))
        return flip

    def movePiece(self):
        legal = self.board.legal_moves
        islegal = False
        move = ""
        #print(legal)
        for item in legal:
            if f"{self.moves[0]}{self.moves[1]}" in self.board.uci(item):
                move = self.board.uci(item)
                #print(self.board.uci(item))
                islegal = True
                break
        # move

        if islegal:
            # make the move
            
            promote = ['q', 'r', 'b','n']
            
            action = None
            r = ""
          
            if str(move)[-1] in promote:
                print("promoting")
                
                pr = customtkinter.CTkToplevel(self.master)
                
                pr.title("Promotion")
                pr.geometry("300x300")
                pr.resizable(False, False)

                l = customtkinter.CTkLabel(pr, text="What piece to promote to?")
                l.pack(side="top", padx=40, pady=20)

                choice = IntVar()
                #style = ttk.Style()
                #style.configure('W.TButton', borderwidth=0)


                btn1 = customtkinter.CTkButton(pr, text="Queen", command=lambda: choice.set(0))
                btn1.pack(side="top", padx=40, pady=10)
                
    
                btn2 = customtkinter.CTkButton(pr, text="Rook", command=lambda: choice.set(1))
                btn2.pack(side="top", padx=40, pady=10)
                

                btn3 = customtkinter.CTkButton(pr, text="Bishop", command=lambda: choice.set(2))
                btn3.pack(side="top", padx=40, pady=10)
                
    
                btn4 = customtkinter.CTkButton(pr, text="Knight", command=lambda: choice.set(3))
                btn4.pack(side="top", padx=40, pady=10)

                pr.wait_variable(choice)
                

                pr.destroy()
                r = f"{self.moves[0]}{self.moves[1]}{promote[choice.get()]}"
                action = chess.Move.from_uci(r)
           
            else:
                r = f"{self.moves[0]}{self.moves[1]}"
                action = chess.Move.from_uci(r)

            self.move(r, action)
            

        else:
            self.reset() # illegal move
     

    def updateMoveslist(self, ind, append, iscapture, isE):



        self.MovesList.configure(state="normal")
        i = len(self.moveHistory) - 1
        if append:
            if isE:
                if self.player == 0:
                    self.wCaptures += str(1)
                else:
                    self.bCaptures += str(1)
            elif iscapture:
                if self.player == 0:
                    self.wCaptures += str(self.board.piece_type_at(self.board.parse_san(self.moveHistory[i][2]).to_square))
                else:
                    self.bCaptures += str(self.board.piece_type_at(self.board.parse_san(self.moveHistory[i][2]).to_square))

                self.updateCaptures()
            
            if i % 2 == 0:    
                self.MovesList.insert(END, f" {self.moveHistory[i][2]} ")
            else:
                
                self.MovesList.insert(END, f"{int(i/2) + 1}. {self.moveHistory[i][2]}")

            self.MovesList.configure(state="disabled")
        
            self.MovesList.see("end")
            return
        
        #seeking only?
        self.MovesList.delete('1.0', END)
        #print(self.moveHistory)
        

        for i in range(len(self.moveHistory)):
            self.piecesB = ''
            self.piecesB = ''
            if i <= ind:
                #print(i)
                if i == 0:
                    continue
                b = chess.Board(self.moveHistory[i][0])
                if b.is_en_passant(b.parse_san(self.moveHistory[i][2])):
                    if self.player == 0:
                        self.wCaptures += str(1)
                    else:
                        self.bCaptures += str(1)
                elif b.is_capture(b.parse_san(self.moveHistory[i][2])):
                    if self.player == 0:
                        self.wCaptures += str(b.piece_type_at(b.parse_san(self.moveHistory[i][2]).to_square))
                    else:
                        self.bCaptures += str(b.piece_type_at(b.parse_san(self.moveHistory[i][2]).to_square))

                if i % 2 == 0:    
                    self.MovesList.insert(END, f" {self.moveHistory[i][2]} ")
                else:
                    
                    self.MovesList.insert(END, f"{int(i/2) + 1}. {self.moveHistory[i][2]}")

        #self.updateCaptures()

        self.MovesList.configure(state="disabled")
        
        self.MovesList.see("end")

    def updateCaptures(self):
        self.wCaptures = ''.join(sorted(self.wCaptures, reverse=True))
        self.bCaptures = ''.join(sorted(self.bCaptures, reverse=True))
        #print(self.wCaptures)
        #print(self.bCaptures)
        diff = sum([self.values[int(x)-1] for x in self.wCaptures]) - sum([self.values[int(x)-1] for x in self.bCaptures])
        b = ''
        w = ''
        if diff > 0:
            w = f" +{str(abs(diff))}"
        elif diff < 0:
            b = f" +{str(abs(diff))}"

        self.captures2.configure(text=''.join([self.piecesW[x] for x in self.wCaptures]) + w) 
        self.captures1.configure(text=''.join([self.piecesB[x] for x in self.bCaptures]) + b) 
        

    def seek(self, ind):
        
        if ind < 0 or ind > (len(self.moveHistory) - 1): # if out of bounds
            return

        #iscapture = chess.Board(self.moveHistory[ind][0]).is_capture(self.moveHistory[ind][2])

        if ind != (len(self.moveHistory) - 1): # if not newest one
            self.seeking = True
        else: # if newest one
            self.seeking = False
            self.seekind = (len(self.moveHistory) - 1)
            self.updateMoveslist(self.seekind, False, False, False) # dont worry about captures or enpassant here since it is calculated during seek
            self.reset()
            return

        self.seekind = ind

        self.createBoard(self.moveHistory[ind][0], self.moveHistory[ind][1], self.isflip())
        
        self.updateMoveslist(ind, False, False, False)
        pass

    def drawlegalMoves(self, ignorePiece, flipped):
        move = self.moves[0]
        legal = self.board.legal_moves
        legal_moves = []
        for item in legal:

                
            if move == self.board.uci(item)[:2]:
                
                
                promote = ['q', 'r', 'b',' n']
                if str(item)[-1] in promote:
                    #print(item)
                    legal_moves.append(str(item).replace(str(move), "")[:-1])
                else:
                    legal_moves.append(str(item).replace(str(move), ""))
        
        #print(legal_moves)


        for i in range(8): # columns 
            for j in range(8): # rows
                color = ["#646E40", "#829769"]
                default = ["#F0D9B5", "#B58863"]
                ind = 0
                opp = 1
                if (i+j) % 2 != 0:
                    ind = 1
                    opp = 0
                    #print("white")
                
                #if flipped:
                #    i = 7-i
                #    j = j

                #pos = f"{chr(i+97)}{8-j}" # square in chess notation
                if self.isflip():
                    #x = 7-x
                    #y = 7-y
                    pos = f"{chr((7-i)+97)}{j+1}"
                    p = self.findPiece(7-i, 7-j, self.board.fen())
                else:
                    pos = f"{chr(i+97)}{8-j}" # square in chess notation
                    p = self.findPiece(i, j, self.board.fen())
                

                
                if pos == move:
                    
                
                    self.w.create_rectangle(i*self.BLOCKX, j*self.BLOCKY, (i+1)*self.BLOCKX, (j+1)*self.BLOCKY, fill=color[opp], outline = '')
                    if ignorePiece == False:
                        path = f"{os.getcwd()}\\images\\{p}.png"
                        #print(path)
                        self.img.append(PhotoImage(file = path))
                        
                        self.w.create_image(i*self.BLOCKX + self.BLOCKX/2-1, (j)*self.BLOCKY + self.BLOCKY/2-1, image=self.img[-1])

                if pos in legal_moves:

                    #print(pos)
                    if p != "none":
                        
                        self.w.create_rectangle(i*self.BLOCKX, j*self.BLOCKY, (i+1)*self.BLOCKX, (j+1)*self.BLOCKY, fill=default[ind], outline = '')
                        self.w.create_oval(i*self.BLOCKX+5, j*self.BLOCKY+5, i*self.BLOCKX+70, j*self.BLOCKY+70, fill='', outline=color[opp], width=10)
                        path = f"{os.getcwd()}\\images\\{p}.png"
                        #print(path)
                        self.img.append(PhotoImage(file = path))
                        
                        self.w.create_image(i*self.BLOCKX + self.BLOCKX/2-1, (j)*self.BLOCKY + self.BLOCKY/2-1, image=self.img[-1])
                    else:
                        self.w.create_oval(i*self.BLOCKX+30, j*self.BLOCKY+30, i*self.BLOCKX+45, j*self.BLOCKY+45, fill=color[opp], outline='')

        self.w.pack()

        



    def findPiece(self, x, y, fen):
        fenB = fen.split(' ')[0]
        file = 0
        rank = 7


        for i in fenB:
            if i == '/':
                file = 0
                rank -= 1
            else:
                if i.isdigit():
                    file += int(i)
                else:
                    f = "b"
                    if i.isupper():
                        f = "w"

                    #print(i)

                    
                    if (file == x and 7-rank == y):
                        #print(f"found: {x},{y}")
                        return f"{f}{i.upper()}"
                    file += 1

        return "none"


    def createBoard(self, fen, prevmove, flipped = False):
        self.img = []
        


            
        for i in range(8): # columns 
            for j in range(8): # rows
                color = ["#F0D9B5", "#B58863"]
                moved = ["#CDD26A", "#AAA23A"]
                ind = 0
                opp = 1
                if (i+j) % 2 != 0:
                    ind = 1
                    opp = 0
                    #print("white")
                if flipped:
                    pos = f"{chr((7-i)+97)}{j+1}"
                else:
                    pos = f"{chr(i+97)}{8-j}" # square in chess notation


                if pos in prevmove:
                    self.w.create_rectangle(i*self.BLOCKX, j*self.BLOCKY, (i+1)*self.BLOCKX, (j+1)*self.BLOCKY, fill=moved[ind], outline = '')
                else:
                    self.w.create_rectangle(i*self.BLOCKX, j*self.BLOCKY, (i+1)*self.BLOCKX, (j+1)*self.BLOCKY, fill=color[ind], outline = '')

                if i == 0:
                    if flipped:
                        self.w.create_text(10, j*self.BLOCKY+10, text=str(j+1), fill=color[opp], font=('Helvetica 10'))
                    else:
                        self.w.create_text(10, j*self.BLOCKY+10, text=str(8-j), fill=color[opp], font=('Helvetica 10'))

                if j == 7:
                    if flipped:
                        self.w.create_text((i+1)*self.BLOCKX - 10, j*self.BLOCKX + 65, text=chr((7-i)+97), fill=color[opp], font=('Helvetica 10'))
                    else:
                        self.w.create_text((i+1)*self.BLOCKX - 10, j*self.BLOCKX + 65, text=chr(i+97), fill=color[opp], font=('Helvetica 10'))

        fenB = fen.split(' ')[0]
        if flipped:
            fenB = str(fenB)[::-1]
        file = 0
        rank = 7
        self.w.pack()

        for i in fenB:
            if i == '/':
                file = 0
                rank -= 1
            else:
                if i.isdigit():
                    file += int(i)
                else:
                    f = "b"
                    if i.isupper():
                        f = "w"

                    if "k" in i.lower() and self.board.is_check() and ((f == "b" and self.checked[0] == 0) or (f == "w" and self.checked[0] == 1)):
                        c = "#e9352d"
                        self.w.create_rectangle(file*self.BLOCKX, (7-rank)*self.BLOCKY, (file+1)*self.BLOCKX, (7-rank+1)*self.BLOCKY, fill=c, outline = '')

                    path = f"{os.getcwd()}\\images\\{f}{i.upper()}.png"
                    #print(path)
                    self.img.append(PhotoImage(file = path))
                    
                    self.w.create_image(file*self.BLOCKX + self.BLOCKX/2-1, (7-rank)*self.BLOCKY + self.BLOCKY/2-1, image=self.img[-1])
                    
                    file += 1


if __name__ == '__main__':
    b = chess_GUI()      




    