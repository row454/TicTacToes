import socket as s
import urllib.request

external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')

print(external_ip)

rooms = {}

port = 2000
ip = "127.0.0.1"
with s.socket(s.AF_INET, s.SOCK_STREAM) as server:
    server.bind((ip, port))
    server.listen()
    while True:
        print(rooms)
        conn, addr = server.accept()
        args = [None, None]
        args[0] = conn.recv(128).decode("utf-8")
        print("received " + args[0])
        if args[0] in rooms:
            conn.sendall(rooms[args[0]].encode("utf-8"))
        else:
            print("sending f")
            conn.send(bytes((0).to_bytes(1, "little")))
            print("sent f")
        args[1] = conn.recv(128)
        if args[1] != b'\x00' and args[1] != b'\x01':
            rooms.update({args[0]: args[1].decode("utf-8")})
        elif args[1] == b'\x01':
            rooms.pop(args[0])
        conn.close()

input()
