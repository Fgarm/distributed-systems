'''
O código age como um servidor TCP que segue as especifícações mostradas em pdf,
permitindo a navegação no sistema de arquivos do servidor por clientes autenticados
Autor: Guilherme Augusto Rodrigues Maturana
Data de criação: 11/09/2023
'''

import os
import signal
import socket
import pathlib
from threading import Thread
import hashlib
HOST = "127.0.0.1" 
PORT = 33333  
userbase = {}
ORIGINAL_DIR = os.getcwd()

# Quando uma Thread é criada com essa função, ela fica responsável por atender as requisições de um cliente
def clientConnection(conn: socket.socket, addr) -> None:
    cur_dir = ORIGINAL_DIR
    username = ''
    allowed = False
    with conn:
            print(f"Connected by {addr}")
            while True:
                data = bytearray()
                try:
                    data.extend(conn.recv(1024))
                except ConnectionAbortedError:
                    print(f"{addr} went away")
                    exit()
                if data:
                    message = data.decode()
                    print(f"data type is {type(data)}")
                    print(f"{addr} : |{message}|")
                    if message == "EXIT":
                        print("EXITing client communication")
                        message = "You should not receive this"
                        break
                    elif allowed:
                        if message == "PWD":
                            message = cur_dir
                            if os.name == 'nt':
                                message = pathlib.PureWindowsPath(cur_dir).as_posix()
                            
                        elif message.startswith("CHDIR "):
                            path = message.split()[1:]
                            path = ' '.join(path)
                            path = os.path.normpath(path)
                            message = "Error in path change"
                            try:
                                os.chdir(path)
                                cur_dir = os.getcwd()
                                os.chdir(ORIGINAL_DIR)
                                print(f"path: {cur_dir}")
                                message = " "
                            except FileNotFoundError:
                                print("Directory: {0} does not exist".format(path))
                            except NotADirectoryError:
                                print("{0} is not a directory".format(path))
                            except PermissionError:
                                print("No permissions to change to {0}".format(path))
                        
                        elif message == "GETFILES":
                            message = ''
                            for file in os.scandir(cur_dir):
                                if file.is_file():
                                    message = message + os.path.basename(file) + "\n"
                            message = message[:-1]
                            
                        elif message == "GETDIRS":
                            message = ''
                            for file in os.scandir(cur_dir):
                                if file.is_dir():
                                    message = message + os.path.basename(file) + "\n"
                            message = message[:-1]
                        
                        elif message.startswith("CHDIR"):
                            message = "Wrong Usage"
                            
                        elif message.startswith("CONNECT "):
                            message = f"Already logged in as {username}"
                        else:
                            message = "Not a valid command"
                    else:
                        if message.startswith("CONNECT "):
                            parameters = message[7:]
                            try:
                                user, password = parameters.replace(" ", "").split(",")
                                if userbase[user] == password:
                                    allowed = True
                                    username = user
                                    message = "SUCCESS"
                                else:
                                    message = "ERROR"
                            except ValueError:
                                message = "Wrong format"
                            except KeyError:
                                message = "ERROR"
                        else:
                            message = "Please log in.\nUsage: CONNECT user, password"
                            
                    
                    data = message.encode()
                    conn.sendall(data)
                    
                    
                    

def __close(signum, frame):
    exit(1)
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, __close)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0)
        userbase["root"] = hashlib.sha512("root".encode('UTF-8')).hexdigest()
        userbase["admin"] = hashlib.sha512("admin".encode('UTF-8')).hexdigest()
        userbase["user"] = hashlib.sha512("123mudar".encode('UTF-8')).hexdigest()
        while True:
            try:
                conn, addr = s.accept() 
                new_thread = Thread(target=clientConnection,args=(conn, addr))
                new_thread.start()
            except TimeoutError:
                pass 
