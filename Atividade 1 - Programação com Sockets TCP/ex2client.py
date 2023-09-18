'''
O código age como um cliente TCP que segue as especifícações mostradas em pdf,
permitindo navegação no sistema de arquivos do servidor e cópia de arquivos
Autor: Guilherme Augusto Rodrigues Maturana
Data de criação: 11/09/2023
Data de ultima modificação: 18/09/2023
'''

import socket
import hashlib

HOST = "127.0.0.1"
PORT = 33333 
REQUEST_CODE = 0x01

# implementa o requerimento addfile
def request_addfile(message: str, request: bytearray):
    request.extend((0x01).to_bytes(1, 'big')) # Command Identifier
    parameters = message[7:] 
    try:
        filename, file_content = parameters.strip().split(",")
    except ValueError:
        raise ValueError("Wrong format")
        
    filename = filename.strip()
    file_content = file_content.lstrip()
    if len(filename.encode('utf-8')) > 255:
        raise NameError("Too Long filename")
    
    request.extend(len(filename.encode('utf-8')).to_bytes(1, 'big')) # Filename Size
    request.extend(filename.encode('utf-8'))
    
    if len(file_content.encode('utf-8')) > (2**32):
        raise OverflowError("File too big")
    request.extend(len(file_content.encode('utf-8')).to_bytes(4, 'big'))
    request.extend(file_content.encode('utf-8'))
    
# implementa o requerimento delete
def request_delete(message: str, request: bytearray):
    request.extend((0x02).to_bytes(1, 'big')) # Command Identifier
    filename = message[6:]
    filename = filename.strip()
    if len(filename.encode('utf-8')) > 255:
        raise NameError("Too Long filename")
    
    request.extend(len(filename.encode('utf-8')).to_bytes(1, 'big')) # Filename Size
    request.extend(filename.encode('utf-8'))
    
# implementa o requerimento getfileslist
def request_getfileslist(message: str, request: bytearray):
    request.extend((0x03).to_bytes(1, 'big')) # Command Identifier
    request.extend((0).to_bytes(1, 'big')) # Filename Size
    
# implementa o requerimento getfile
def request_getfile(message: str, request: bytearray):
    request.extend((0x04).to_bytes(1, 'big')) # Command Identifier
    filename = message[7:]
    filename = filename.strip()
    if len(filename.encode('utf-8')) > 255:
        raise NameError("Too Long filename")
    
    request.extend(len(filename.encode('utf-8')).to_bytes(1, 'big')) # Filename Size
    request.extend(filename.encode('utf-8'))

# implementa o requerimento de conexão, não implementado no servidor e desativado no cliente
def request_connect(message: str, request: bytearray):
    request.extend((0x05).to_bytes(1, 'big')) # Command Identifier
    # falta o Filename Size
    parameters = message[7:]
    try:
        user, password = parameters.replace(" ", "").split(",")
    except ValueError:
        print("Wrong format")
    hashed_password = hashlib.sha512(password.encode('UTF-8')).hexdigest()
    request.extend((len(user.encode('utf-8'))).to_bytes(1, 'big'))
    request.extend(user.encode('utf-8'))
    request.extend((len(hashed_password.encode('utf-8'))).to_bytes(1, 'big'))
    request.extend(hashed_password.encode('utf-8'))
    
# implementa o requerimento pwd
def request_pwd(message: str, request: bytearray):
    request.extend((0x06).to_bytes(1, 'big')) # Command Identifier
    request.extend((0).to_bytes(1, 'big'))  # Filename Size
    
# implementa o requerimento chdir
def request_chdir(message: str, request: bytearray):
    request.extend((0x07).to_bytes(1, 'big')) # Command Identifier
    path = message[5:]
    path = path.strip()
    if len(path.encode('utf-8')) > 255:
        raise NameError("Path too big")
    request.extend(len(path.encode('utf-8')).to_bytes(1, 'big')) # Filename Size
    request.extend(path.encode('utf-8'))
    
# implementa o requerimento getfiles, não implementado no servidor e desativado no cliente
def request_getfiles(message: str, request: bytearray):
    request.extend((0x08).to_bytes(1, 'big')) # Command Identifier
    request.extend((0).to_bytes(1, 'big'))
    
# implementa o requerimento getdirs, não implementado no servidor e desativado no cliente
def request_getdirs(message: str, request: bytearray):
    request.extend((0x09).to_bytes(1, 'big')) # Command Identifier
    request.extend((0).to_bytes(1, 'big'))
    
# implementa o requerimento 
def request_exit(message : str, request: bytearray):
    request.extend((0x0A).to_bytes(1, 'big')) # Command Identifier
    request.extend((0).to_bytes(1, 'big'))

# le e interpreta o cabeçalho básico das respostas do servidor
def interpret_response(S: socket.socket) -> tuple[int, int] | None:
    header = s.recv(3)
    msg_type = header[0:1]
    command = int.from_bytes(header[1:2], 'big')
    status_code = int.from_bytes(header[2:3], 'big')
    if msg_type != (0x02).to_bytes(1, 'big'):
        print("Error: not a response being read")
    else:
        return status_code, command
        
        
        

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        request = bytearray(REQUEST_CODE.to_bytes(1, 'big'))
        message: str = input(">")
        filename = ''
        if message == "PWD":
            request_pwd(message, request)
            
        elif message.startswith("CHDIR "):
            request_chdir(message, request)
            
        elif message == "EXIT":
            request_exit(message, request)
            
        elif message.startswith("ADDFILE "):
            request_addfile(message, request)
            
        elif message.startswith("DELETE "):
            request_delete(message, request)

        elif message.startswith("GETFILESLIST"):
            request_getfileslist(message, request)
            
        elif message.startswith("GETFILE "):
            request_getfile(message, request)
            filename = message[7:]
            filename = filename.strip()
        else:
            print("Invalid Command/Usage!")
            continue

        s.sendall(request)
        if message == "EXIT":
            exit()
        try:
            status_code, command = interpret_response(s)
            if status_code != (0x01):
                print("Error: The requested operation did not perform sucessfully")
                continue
        except ValueError or TypeError:
                    print("Error reading socket")
                    continue
        if command in [0x01, 0x02, 0x07]:
            pass
        elif command == 0x03:
            print("Files in directory:")
            n_arquivos = int.from_bytes(s.recv(2), 'big')
            for i in range(n_arquivos):
                filename_size = int.from_bytes(s.recv(1), 'big')
                filename = s.recv(filename_size).decode('utf-8')
                print(f" • {filename}")
        elif command == 0x04:
            file_size = int.from_bytes(s.recv(4), 'big')
            try:
                with open(file=filename, mode="xb") as f:
                    while f.tell() < file_size:
                        data = s.recv(file_size - f.tell())
                        f.write(data)
            except:
                print("Error creating/reading file")
                
        elif command == 0x06:
            path_size = int.from_bytes(s.recv(2), 'big')
            path = s.recv(path_size).decode('utf-8')
            print(path)
