'''
O código age como um cliente TCP para um servidor que segue as especifícações mostradas em pdf
Autor: Guilherme Augusto Rodrigues Maturana
Data de criação: 11/09/2023
'''

import socket
import hashlib

HOST = "127.0.0.1"
PORT = 33333 

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        message: str = input(">")
        if message.startswith("CONNECT "):
            parameters = message[7:]
            try:
                user, password = parameters.replace(" ", "").split(",")
                hashed_password = hashlib.sha512(password.encode('UTF-8')).hexdigest()
                message = f"CONNECT {user}, {hashed_password}"
            except ValueError:
                print("Wrong format")
                continue
            
        data = message.encode()
        s.sendall(data)
        if message == "EXIT":
            break
        data = bytearray(s.recv(1024))
        print(type(data))
        message = data.decode()
        print(f"{message}")
