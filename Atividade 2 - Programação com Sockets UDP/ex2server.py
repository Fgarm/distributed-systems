
import os
import signal
import socket
import pathlib
import hashlib
from threading import Thread
import logging
import datetime
from time import sleep
import io
senders = []

RECEIVE_IP = "0.0.0.0"
PORT = 33333
# Closes the server in the event of a sigkill, and logs it sucessfull closure
# it waits for any recvfrom to timeout before closing
def __close(signum, frame):
    logging.info(f"Server Exit command sucessful in {datetime.datetime.now()}")
    exit()
    
def commands():
    while True:
        message: str = input(">")
        if message == "PWD":
            if os.name == 'nt':
                print(pathlib.PureWindowsPath(os.getcwd()).as_posix())
            else:
                print(os.getcwd())
            
        elif message.startswith("CHDIR "):
            if not senders:
                os.chdir(os.path.normpath(message[5:].strip()))
                logging.info(f"Download directory changed to \"{os.getcwd()}\"")
            else:
                logging.warning(f"A Download directory change was attempted concurrently to file transfers.")
                print("Error:A file transfer might be happening, can't change dirs")
                
        elif message.startswith("GETFILESLIST"):
            print("Files in directory:")
            for file in os.scandir(os.getcwd()):
                print(f" • {os.path.basename(file)}")
        elif message == "EXIT":
            if not senders:
                signal.raise_signal(signal.SIGINT)
                exit()
            else:
                logging.warning(f"A exit command was attempted concurrently to file transfers.")
                print("Error:A file transfer might be happening, can't exit")
        else:
            print("Invalid Command/Usage!")
            continue

def hey_listen(sender, senders: list, filename: str, file_len: int):
    md5 = hashlib.md5()
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(5.0)
        s.bind(("", PORT))
        try:
            with open(file=os.path.join(os.getcwd(), filename), mode="w+b") as f:
                while f.tell() < file_len:
                    data, origem = s.recvfrom(file_len - f.tell())
                    if origem == sender:
                        f.write(data)
                        md5.update(data)
        except TimeoutError:
            senders.remove(sender)
            print("FAIL")
            logging.warning(f"Download: \"{filename}\" from {sender} finished unsucessfully."
                            "It might be due to packet loss or a stopped client")
            return
        except OSError:
            print("FAIL")
            logging.warning(f'''Download: \"{filename}\" from {sender} finished unsucessfully.''')
            sleep(5)
            senders.remove(sender)
            return
                    
        last_sender = None
        result_hash = md5.hexdigest()
        try:
            while last_sender != sender:
                file_hash, last_sender = s.recvfrom(32)
            if file_hash.decode() == result_hash:
                print("SUCESS")
                logging.info(f"Download: \"{filename}\" from {sender} finished sucessfully.")
            else:
                print("FAIL") # bad data / order
                logging.warning(f"Download: \"{filename}\" from {sender} finished unsucessfully."
                                "It might be due to a bad order of packets or bad data")
        except TimeoutError:
            logging.warning(f"Hash key of \"{filename}\" from {sender} was not received")
        except OSError:
            print("FAIL")
            logging.warning(f'''Download: \"{filename}\" from {sender} finished and retried unsucessfully.''')
        senders.remove(sender)
        


if __name__ == "__main__":
    signal.signal(signal.SIGINT, __close)
    server_start_time = datetime.datetime.now()
    time = f"{server_start_time.hour}-{server_start_time.minute}-{server_start_time.second}"
    logging.basicConfig(filename=f"server-log-{server_start_time.date()}_{time}.log",
                        filemode='w',
                        level=logging.DEBUG,
                        format='%(asctime)s %(name)-5s %(levelname)-5s %(message)s',
                        datefmt='%d-%m %H:%M')
    input_thread = Thread(target=commands)
    input_thread.start()
    os.chdir("..")
    logging.info(f"Server initialized with Download directory \"{os.getcwd()}\".")
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(2.0)
        s.bind(("", PORT))
        while True:
            try:
                message, sender = s.recvfrom(1024)
            except TimeoutError:
                continue
            if sender not in senders:
                try:
                    filename_len = int.from_bytes(message[0:2],'big')
                    filename = message[2:filename_len+2].decode()
                    file_len = int.from_bytes(message[filename_len+2:filename_len+6], 'big')
                    senders.append(sender)
                    logging.info(f"Download: \"{filename}\" from {sender} with {file_len} bytes started")
                    new_thread = Thread(target=hey_listen, args=(sender, senders, filename, file_len))
                    new_thread.start()
                except:
                    continue

