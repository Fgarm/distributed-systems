'''
O código age como um servidor TCP que segue as especifícações mostradas em pdf,
permitindo navegação no sistema de arquivos do servidor e cópia de arquivos.
Os eventos principais ficam armazenados em logs do servidor
Autor: Guilherme Augusto Rodrigues Maturana
Data de criação: 11/09/2023
Data de ultima modificação: 18/09/2023
'''
import os
import signal
import socket
import pathlib
from threading import Thread
import logging
import datetime
HOST = "0.0.0.0" 
PORT = 33333
ORIGINAL_DIR = os.getcwd()
STATUS_CODE_SUCESS = 0x01
STATUS_CODE_ERROR = 0x02

# interpreta o cabeçalho básico dos requerimentos
def interpret_header(conn: socket.socket, addr) -> tuple[int, str] | None:
    header = conn.recv(3)
    msg_type = header[0:1]
    filename_size = 0
    if msg_type != (0x01).to_bytes(1, 'big'):
        logging.warning(f"A message that was not a request came from {addr}")
    else:
        command = int.from_bytes(header[1:2], byteorder='big')
        filename_size = int.from_bytes(header[2:3], byteorder='big')
        filename = ''
        if filename_size != 0:
            filename = conn.recv(filename_size)
            filename = filename.decode('utf-8')
        
        if command == (0x0A):
            logging.info(f"Connection with {addr} was exit sucessfully")
            exit()
        return command, filename

# When a Thread is created with this function, it handles the connection with one client
def clientConnection(conn: socket.socket, addr):
    cur_dir = ORIGINAL_DIR
    with conn:
            logging.info(f"Connected by {addr}")
            while True:
                response = bytearray((0x02).to_bytes(1, 'big')) # says its a response
                try:
                    command, filename = interpret_header(conn, addr)
                    logging.info(f"{addr} sent the command: {command}")
                except ValueError:
                    logging.critical("Error reading socket")
                    exit()
                except TypeError:
                    logging.error(f"{addr} terminated the connection suddenly")
                    exit()
                response.extend(command.to_bytes(1, 'big')) # tells the command type
                if command == (0x01): # addfile
                    try:
                        file_size = int.from_bytes(conn.recv(4), byteorder='big')
                        file = conn.recv(file_size)
                        with open(os.path.join(cur_dir, filename), "w") as f:
                            f.write(file.decode('utf-8'))
                            response.extend(STATUS_CODE_SUCESS.to_bytes(1, 'big'))
                    except:
                        logging.warning("Error in addfile")
                        response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                    
                elif command == (0x02): # delete
                    if len(filename) > 0:
                        if os.path.exists(os.path.join(cur_dir, filename)):
                            os.remove(os.path.join(cur_dir, filename))
                            response.extend(STATUS_CODE_SUCESS.to_bytes(1, 'big'))
                        else:
                            logging.warning("File not found.")
                            response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                    else:
                        logging.warning("No filename")
                        response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                    
                elif command == (0x03): # getfileslist
                    response.extend(STATUS_CODE_SUCESS.to_bytes(1, 'big'))
                    try:
                        n_arquivos = 0
                        response.extend(n_arquivos.to_bytes(2, 'big'))
                        for file in os.scandir(cur_dir):
                            n_arquivos += 1
                            response.extend(len(os.path.basename(file).encode('utf-8')).to_bytes(1, 'big'))
                            response.extend(os.path.basename(file).encode('utf-8'))
                        response[3:5] = n_arquivos.to_bytes(2, 'big')
                    except:
                        logging.warning("Error in getfileslist")
                        response[2:3] = STATUS_CODE_ERROR.to_bytes(1, 'big')
                    
                elif command == (0x04): # getfile
                    if len(filename) > 0:
                        try:
                            with open(os.path.join(cur_dir, filename), "rb") as f:
                                data = f.read()
                            if len(data) > 2**32:
                                response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                            else:
                                response.extend(STATUS_CODE_SUCESS.to_bytes(1, 'big'))
                                response.extend(len(data).to_bytes(4, 'big'))
                                response.extend(data)
                        except:
                            logging.warning("Error in getfile")
                            response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                            
                            
                    else:
                        response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                        logging.warning("No filename")
                    
                elif command == (0x06): # pwd
                    message = cur_dir
                    response.extend(STATUS_CODE_SUCESS.to_bytes(1, 'big'))
                    if os.name == 'nt':
                        message = pathlib.PureWindowsPath(cur_dir).as_posix()
                    response.extend(len(message.encode('utf-8')).to_bytes(2, 'big'))
                    response.extend(message.encode('utf-8'))
                    
                elif command == (0x07): # chdir
                    path = os.path.normpath(filename)
                    try:
                        os.chdir(cur_dir)
                        os.chdir(path)
                        cur_dir = os.getcwd()
                        os.chdir(ORIGINAL_DIR)
                        print(f"path: {cur_dir}")
                        response.extend(STATUS_CODE_SUCESS.to_bytes(1, 'big'))
                    except FileNotFoundError:
                        logging.warning("Directory: {0} does not exist".format(path))
                        response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                    except NotADirectoryError:
                        logging.warning("{0} is not a directory".format(path))
                        response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                    except PermissionError:
                        logging.warning("No permissions to change to {0}".format(path))
                        response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))

                    
                else:
                    logging.warning("Invalid Command Usage")
                    response.extend(STATUS_CODE_ERROR.to_bytes(1, 'big'))
                    continue
                
                conn.sendall(response)
                            
                    
                    
                    
# Closes the server in the event of a sigkill, and logs it sucessfull closure
def __close(signum, frame):
    logging.debug(f"Server Exit sucessful in {datetime.datetime.now()}")
    exit(1)
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, __close)
    server_start_time = datetime.datetime.now()
    time = f"{server_start_time.hour}-{server_start_time.minute}-{server_start_time.second}" 
    logging.basicConfig(filename=f"server-log-{server_start_time.date()}_{time}.log", filemode='w', level=logging.DEBUG)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0)
        while True:
            try:
                conn, addr = s.accept() 
                new_thread = Thread(target=clientConnection,args=(conn, addr))
                new_thread.start()
            except TimeoutError:
                pass 
