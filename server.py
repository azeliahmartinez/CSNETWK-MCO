import socket
import os
import threading
import base64
import time

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
BUFFER_SIZE = 1048576
UPLOADS_FOLDER = 'uploads'

if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen()

print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

def handle_client(client_socket):
    try:
        handle = None
        client_address = client_socket.getpeername()
        print(f"Client connected from {client_address}")

        while True:
            data = client_socket.recv(BUFFER_SIZE)

            if not data:
                break

            decoded_data = data.decode('utf-8', errors='ignore')  # Ignore decoding errors for binary data

            if decoded_data.startswith('/'):
                command, *args = decoded_data.split()

                if command == '/join':
                    handle = args[0]
                    print(f"Client {handle} joined.")

                elif command == '/leave':
                    print(f"Client {handle} disconnected.")
                    break

                elif command == '/register':
                    handle = args[0]
                    client_socket.send(f"Handle registered as {handle}".encode('utf-8'))

                elif command == '/store':
                    filename = args[0]
                    file_data = client_socket.recv(BUFFER_SIZE)

                    with open(os.path.join(UPLOADS_FOLDER, filename), 'wb') as file:
                        file.write(file_data)
                    print(f"File {filename} uploaded by {handle}.")
                    client_socket.send(f"File {filename} uploaded successfully.".encode('utf-8'))

                elif command == '/dir':
                    files = os.listdir(UPLOADS_FOLDER)
                    if files:
                        file_list = "       ".join(files)  # Use newline to separate filenames
                        client_socket.send(file_list.encode('utf-8'))
                        # Signal the end of directory listing after sending it
                    #    client_socket.send("       ".encode('utf-8'))
                   # else:
                     #   client_socket.send("     ".encode('utf-8'))

                    # Clear the buffer
                    received_data = b""

                    # Introduce a small delay
                    time.sleep(3)

                elif command == '/get':
                    filename = args[0]
                    received_data = b""
                    try:
                        with open(os.path.join(UPLOADS_FOLDER, filename), 'rb') as file:
                            received_data = b""
                            file_data = file.read()
                            # Use base64 encoding to send binary data as text
                            encoded_data = base64.b64encode(file_data).decode('utf-8')
                            client_socket.send(encoded_data.encode('utf-8'))
                            client_socket.send("FILE_TRANSFER_COMPLETE".encode('utf-8'))  # Signal the end of file transfer
                    except FileNotFoundError:
                        client_socket.send("FILE_NOT_FOUND".encode('utf-8'))

                elif command == '/?':
                    help_message = """
                    Available Commands:
                    - /join <ip> <port>: Connect to the server
                    - /leave: Disconnect from the server
                    - /register <handle>: Register a unique handle
                    - /store <filename>: Upload a file to the server
                    - /dir: Request a directory list
                    - /get <filename>: Fetch a file from the server
                    - /?: Display help
                    """
                    client_socket.send(help_message.encode('utf-8'))

                else:
                    client_socket.send("Invalid command. Type /? for help.".encode('utf-8'))

            else:
                print(f"Received binary file data from {handle}. Do something with it if needed.")

    except Exception as e:
        print(f"Error handling client: {e}")

    finally:
        print(f"Client {handle} disconnected.")
        client_socket.close()

try:
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

except KeyboardInterrupt:
    print("Server shutting down.")
finally:
    server_socket.close()