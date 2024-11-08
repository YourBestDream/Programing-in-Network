import socket
import threading
import time
import random
from threading import Lock, Condition

# File to be used for read/write operations
FILE_NAME = "shared_file.txt"
file_lock = Lock()
read_condition = Condition()  # Condition variable to coordinate reads and writes
pending_writes = 0  # Counter for active or pending write operations

def handle_client(client_socket):
    global pending_writes
    buffer = ""  # Buffer to accumulate data from the client

    try:
        while True:
            # Receive data from the client
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break

            buffer += data

            # Process complete commands (ending with newline)
            while "\n" in buffer:
                command, buffer = buffer.split("\n", 1)
                command = command.strip()

                if not command:
                    continue

                # Random delay between 1 to 7 seconds
                delay = random.randint(1, 7)
                time.sleep(delay)

                if command.startswith("WRITE"):
                    try:
                        _, data = command.split(" ", 1)
                        with read_condition:
                            pending_writes += 1  # Indicate a write operation is in progress
                        with file_lock:
                            with open(FILE_NAME, "a") as f:
                                f.write(data + "\n")
                        client_socket.sendall(b"Data written to file.\n")
                    except ValueError:
                        client_socket.sendall(b"Invalid WRITE command. Use: WRITE <data>\n")
                    finally:
                        with read_condition:
                            pending_writes -= 1
                            if pending_writes == 0:
                                read_condition.notify_all()  # Notify readers that writes are done

                elif command == "READ":
                    with read_condition:
                        # Wait for all writes to complete
                        while pending_writes > 0:
                            read_condition.wait()
                    with file_lock:
                        try:
                            with open(FILE_NAME, "r") as f:
                                contents = f.read()
                            client_socket.sendall(contents.encode("utf-8") + b"\n")
                        except FileNotFoundError:
                            client_socket.sendall(b"File not found.\n")

                else:
                    client_socket.sendall(b"Invalid command. Use WRITE <data> or READ.\n")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

def start_tcp_server(host="0.0.0.0", port=6000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"TCP server listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"Connection established with {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_tcp_server()
