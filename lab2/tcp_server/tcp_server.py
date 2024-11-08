import socket
import threading
import time
from random import randint

lock = threading.Lock()
data_file = 'shared_data.txt'

def handle_client(conn, addr):
    with conn:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            with lock:
                if data.startswith('write'):
                    with open(data_file, 'a') as f:
                        f.write(f'{addr}: {data}\n')
                    time.sleep(randint(1, 7))
                    conn.sendall(b'Write operation completed\n')
                elif data.startswith('read'):
                    with open(data_file, 'r') as f:
                        content = f.read()
                    conn.sendall(content.encode())

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 65432))
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
