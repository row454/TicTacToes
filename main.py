import tkinter as tk
from contextlib import suppress
from tkinter.messagebox import showinfo, showerror

import socket
import socket as s
from select import select
import pickle


# Tic Tac Toe


class Game:

    def __init__(self, mode):

        self.mode = mode

        # Nothing = -1, Cross = 0, Nought = 1
        self.teams = ("Crosses", "Noughts")
        self.board = [
            [-1, -1, -1],
            [-1, -1, -1],
            [-1, -1, -1]
        ]

        self.turn = 0

        self.window = tk.Tk()
        self.window.configure(bg="white")
        self.window.resizable(False, False)

        self.images = [tk.PhotoImage(file="blank.png"), tk.PhotoImage(file="cross.png"),
                       tk.PhotoImage(file="nought.png")]

        # -1 = not connected, 0 = client or against ai, 1 = server
        self.role = -1
        if mode == 2:
            self.socket = None
            self.connection = None
            self.frm_connect = tk.Frame(self.window)

            ent_ip = tk.Entry(self.frm_connect)
            btn_connect = tk.Button(self.frm_connect, text="Connect", command=lambda: self.connect(ent_ip.get()))
            ent_ip.pack()
            btn_connect.pack()
            self.frm_connect.pack()
            while self.socket is None:
                self.window.update()

        if mode == 3:
            self.role = 0

        if mode == 4:
            self.socket = None
            self.connection = None
            hostname = socket.gethostbyname(socket.gethostname())
            self.frm_connect = tk.Frame(self.window)

            ent_room = tk.Entry(self.frm_connect)

            frm_buttons = tk.Frame(self.frm_connect)
            btn_new_room = tk.Button(frm_buttons, text="Host room",
                                     command=lambda: ent_room.get() == "" or (self.add_room(ent_room.get()) and self.connect(hostname)))
            btn_connect = tk.Button(frm_buttons, text="Connect",
                                    command=lambda: ent_room.get() == "" or (self.is_room(ent_room.get()) and self.connect(self.get_room(ent_room.get()))))

            ent_room.pack()
            frm_buttons.pack()
            btn_new_room.pack(side=tk.LEFT)
            btn_connect.pack(side=tk.LEFT)
            self.frm_connect.pack()
            while self.socket is None:
                self.window.update()

        frm_buttons = tk.Frame(self.window)

        btn_exit = tk.Button(frm_buttons, text="Exit", command=self.exit)
        btn_menu = tk.Button(frm_buttons, text="Menu", command=self.back_to_menu)

        btn_exit.pack(side=tk.LEFT)
        btn_menu.pack(side=tk.LEFT)

        frm_board = tk.Frame(self.window)

        self.spaces = [
            [-1, -1, -1],
            [-1, -1, -1],
            [-1, -1, -1]
        ]
        for y in range(3):
            for x in range(3):
                frame = tk.Frame(
                    master=frm_board,
                    relief=tk.RAISED,
                    borderwidth=1,
                    width=400,
                    height=400
                )
                frame.grid(row=y, column=x)

                self.spaces[y][x] = tk.Label(master=frame, image=self.images[0])
                self.spaces[y][x].pack()
                self.spaces[y][x].bind('<Button-1>', lambda e, x=x, y=y: self.place(x, y))

        frm_buttons.pack()
        frm_board.pack()

        if self.role == 1:
            for i in range(3):
                for j in range(3):
                    self.spaces[i][j].config(state=tk.DISABLED)
                    self.spaces[i][j].unbind("<Button-1>")
                    self.spaces[i][j].update_idletasks()
            opponent_move = None
            while opponent_move is None:

                readable, writable, exceptional = select([self.connection], [], [], 0)
                self.window.update()
                for s in readable:
                    opponent_move = s.recv(20)
                    print(opponent_move)
                    opponent_move = pickle.loads(opponent_move)
                    self.place(opponent_move[0], opponent_move[1])

        self.window.mainloop()

    def place(self, x, y):

        if self.board[y][x] == -1:
            self.board[y][x] = self.turn % 2
            self.spaces[y][x].configure(image=self.images[self.turn % 2 + 1])

            if (self.mode == 2 or self.mode == 4) and self.turn % 2 == self.role:
                print(pickle.dumps([x, y]))
                self.connection.sendall(pickle.dumps([x, y]))

            winner = self.winner()
            if winner is not None:
                if winner == 0:
                    showinfo("Game Over!", "The game is a draw!")
                else:
                    showinfo("Game Over!", "The " + self.teams[(winner + 3) // 2 - 1] + " have won!")
                self.back_to_menu()
                return

            self.turn += 1
            self.window.update()

            if self.mode != 1:
                for i in range(3):
                    for j in range(3):
                        self.spaces[i][j].config(state=tk.DISABLED)
                        self.spaces[i][j].unbind("<Button-1>")
                        self.spaces[i][j].update_idletasks()

            if (self.mode == 2 or self.mode == 4) and self.turn % 2 != self.role:
                opponent_move = None
                while opponent_move is None:

                    readable, writable, exceptional = select([self.connection], [], [], 0)
                    self.window.update()
                    for s in readable:
                        opponent_move = s.recv(20)
                        print(opponent_move)
                        opponent_move = pickle.loads(opponent_move)
                        self.place(opponent_move[0], opponent_move[1])

            if self.mode == 3 and self.turn % 2 != self.role:
                self.ai_move()

            if self.mode != 1:
                with suppress(tk.TclError):
                    for i in range(3):
                        for j in range(3):
                            self.spaces[i][j].config(state=tk.ACTIVE)
                            self.spaces[i][j].bind("<Button-1>", lambda e, x=j, y=i: self.place(x, y))
                            self.spaces[i][j].update_idletasks()

    def ai_move(self):
        best_move = [-1, -1]
        max_score = -1000
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == -1:
                    self.board[i][j] = self.turn % 2
                    score = self.minmax(self.board, 0, self.turn + 1)
                    self.board[i][j] = -1
                    if score > max_score:
                        max_score = score
                        best_move = [i, j]
        self.place(best_move[1], best_move[0])

    def add_room(self, name):
        with s.socket(s.AF_INET, s.SOCK_STREAM) as socket:
            socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
            socket.connect(("127.0.0.1", 2000))
            socket.sendall(name.encode("utf-8"))
            data = socket.recv(128)
            if data != b'\x00':
                showerror("bad room name", "invalid room name, its already in use")
                socket.sendall((0).to_bytes(1, "little"))
                return False
            else:
                socket.sendall(s.gethostbyname(s.gethostname()).encode("utf-8"))
                return True

    def get_room(self, name):
        with s.socket(s.AF_INET, s.SOCK_STREAM) as socket:
            socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
            socket.connect(("127.0.0.1", 2000))
            socket.sendall(name.encode("utf-8"))
            data = socket.recv(128)
            print(data.decode("utf-8"))
            socket.sendall((1).to_bytes(1, "little"))
            if data == b'\x00':
                print("invalid room name, its not in use")
                return
            else:
                return data.decode("utf-8")


    def is_room(self, name):
        with s.socket(s.AF_INET, s.SOCK_STREAM) as socket:
            socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
            socket.connect(("127.0.0.1", 2000))
            socket.sendall(name.encode("utf-8"))
            data = socket.recv(128)
            print(data.decode("utf-8"))
            socket.sendall((0).to_bytes(1, "little"))
            if data == b'\x00':
                return False
            else:
                return True

    def connect(self, ip):
        if self.role != -1:
            print("no")
            return False
        localhost = "0.0.0.0"
        try:
            s.inet_aton(ip)
        except s.error:
            showerror("Invalid IP", "The IP address that was entered is invalid")
            return False

        port = 4000

        socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        if socket.connect_ex((ip, 4000)) == 0:
            try:
                socket.sendall("".encode("utf-8"))
                self.role = 0
                self.frm_connect.destroy()
                self.socket = socket
                self.connection = socket
                return False
            except Exception as e:
                print(e)
                showerror("Server closed the connection", "The IP you entered doesn't accept your IP")
                return False

        else:
            socket = s.socket(s.AF_INET, s.SOCK_STREAM)
            socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
            self.role = 1
            print(socket)
            socket.bind((localhost, port))
            socket.listen()
            while True:
                conn, addr = socket.accept()
                if addr[0] == ip:
                    self.frm_connect.destroy()
                    self.socket = socket
                    self.connection = conn
                    return False
                else:
                    conn.close()

        return False

    def exit(self):
        if mode == 2 or mode == 4:
            if self.socket is not None:
                self.socket.close()
        self.window.destroy()
        exit(0)

    def back_to_menu(self):
        if mode == 2 or mode == 4:
            if self.socket is not None:
                self.socket.close()
        self.window.destroy()

    def winner(self, board=None):
        # Returns: 1 for nought win, 0 for tie, -1 for cross win, None otherwise
        if board is None:
            board = self.board

        for i in range(3):
            if board[i][0] >= 0 and board[i][0] == board[i][1] and board[i][0] == board[i][2]:
                return (board[i][0] + 1) * 2 - 3

            if board[0][i] >= 0 and board[0][i] == board[1][i] and board[0][i] == board[2][i]:
                return (board[0][i] + 1) * 2 - 3

        if board[0][0] >= 0 and board[0][0] == board[1][1] and board[0][0] == board[2][2]:
            return (board[0][0] + 1) * 2 - 3
        if board[2][0] >= 0 and board[2][0] == board[1][1] and board[2][0] == board[0][2]:
            return (board[2][0] + 1) * 2 - 3

        tie = True
        for i in range(3):
            for j in range(3):
                if board[i][j] == -1:
                    tie = False

        if tie:
            return 0
        else:
            return None

    def minmax(self, board, depth, turn):
        win = self.winner(board)
        if win is not None:
            return win * 10 - depth * win

        if turn % 2:
            max_score = -1000
            for i in range(3):
                for j in range(3):
                    if board[i][j] == -1:
                        board[i][j] = turn % 2
                        score = self.minmax(board, depth + 1, turn + 1)
                        board[i][j] = -1
                        if score > max_score:
                            max_score = score
        else:
            max_score = 1000
            for i in range(3):
                for j in range(3):
                    if board[i][j] == -1:
                        board[i][j] = turn % 2
                        score = self.minmax(board, depth + 1, turn + 1)
                        board[i][j] = -1
                        if score < max_score:
                            max_score = score
        return max_score


print("Welcome to Tic-Tac-Toes!")

while True:
    print("What mode would you like to play?", "1: Against a local player", "2: IP multiplayer",
          "3: Against an unbeatable ai", "4: Room name multiplayer", sep="\n")
    try:
        mode = int(input("--> "))
        if mode < 5:
            Game(mode)
        else:
            raise Exception()
    except Exception as e:
        print(e)
        print("Invalid input")
        continue
