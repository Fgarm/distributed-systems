import os
import socket
import pathlib
import hashlib
from time import sleep
from math import floor

serverAddressPort = ("<broadcast>", 33333)

SHOULD_WORK_IN_PARALLEL = 0


with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as s:
    
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        message: str = input(">")
        if message == "PWD":
            if os.name == 'nt':
                print(pathlib.PureWindowsPath(os.getcwd()).as_posix())
            else:
                print(os.getcwd())
            
        elif message.startswith("CHDIR "):
            try:
                os.chdir(os.path.normpath(message[5:].strip()))       
            except FileNotFoundError:
                print("Directory does not exist")
                continue
            
        elif message.startswith("GETFILESLIST"):
            print("Files in directory:")
            for file in os.scandir(os.getcwd()):
                print(f" • {os.path.basename(file)}")
                
        elif message.startswith("ADDFILE "):
            parameters = message[7:]
            filename_pure = parameters.strip()
            try:
                filename = os.path.join(os.getcwd(), filename_pure)
            except FileNotFoundError:
                print(f"File does not exist")
                continue
            
            if len(filename_pure.encode('utf-8')) > 255:
                print("Too Long filename")
                continue
            print(f"[{' ' * 25}] {'0%':>7}", end='')
            request = bytearray(len(filename_pure.encode('utf-8')).to_bytes(2, 'big'))
            request.extend(filename_pure.encode('utf-8'))
            
            with open(filename, "rb") as f:
                data = f.read()
                file_len = len(data) # get size
                hash = hashlib.md5(data).hexdigest() # get hash
                if file_len > 2**32:
                    print("File too big né")
                    continue
                else:
                    request.extend(file_len.to_bytes(4, 'big'))
            s.sendto(request, serverAddressPort)
            # print(f"\nrequest:\n{request}\n")
            
            with open(filename, "rb") as f:
                    while(f.tell() < file_len):
                        if(file_len - f.tell()) > 1024:
                            chunk = f.read(1024)
                        else:
                            chunk = f.read(file_len - f.tell())
                        if SHOULD_WORK_IN_PARALLEL:
                            print(f"\n{chunk}\n")
                        else:
                            sleep(0.001)
                        s.sendto(chunk, serverAddressPort)
                        percent: int = ((f.tell() * 25) / file_len)
                        print(f"\r[{'-' * (floor(percent))}{' ' * (25 - (floor(percent)))}] {f'{percent*4:.2f}%':>7}", end='')
            s.sendto(hashlib.md5(data).hexdigest().encode(), serverAddressPort)
            print("")
            
        elif message == "EXIT":
            exit()
        else:
            print("Invalid Command/Usage!")
            continue