import socket
import struct
import os
import base64

BUFFER_SIZE = 1048576

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(10)  # Set a timeout of 10 seconds for connecting to the server

handle = None  # Store the user's handle
connected = False  # Flag to track the connection status
registered = False  # Flag to track the registration status


def display_help():
    print("""
    Available Commands:
    - /join <ip> <port>: Connect to the server
    - /leave: Disconnect from the server and exit
    - /register <handle>: Register a unique handle (requires server connection)
    - /store <filename>: Upload a file to the server (requires registration)
    - /dir: Request a directory list (requires registration)
    - /get <filename>: Fetch a file from the server (requires registration)
    - /?: Display help
    """)

def main():
    global handle, connected, registered

    try:
        while True:
            user_input = input("Enter a command: ")

            if user_input.lower() == '/leave':
                if not connected:
                    print("You are not connected to any server.")
                else:
                    client_socket.send("/leave".encode('utf-8'))
                    print("Leaving the server. Goodbye!")
                    break

            elif user_input.startswith('/join'):
                if connected:
                    print("Already connected to a server. Use /leave to disconnect first.")
                else:
                    try:
                        _, server_ip, server_port = user_input.split()
                        SERVER_ADDRESS = (server_ip, int(server_port))
                        client_socket.settimeout(10)  # Set a timeout of 10 seconds for connecting to the server
                        client_socket.connect(SERVER_ADDRESS)
                        print(f"Connected to server at {server_ip}:{server_port}")
                        connected = True
                    except ValueError:
                        print("Invalid IP/port. Please provide a valid IP and port.")
                    except socket.timeout:
                        print(f"Error connecting to the server: Connection timed out. The server may be unreachable.")
                    except socket.error as e:
                        if "10061" in str(e):
                            print(f"Error connecting to the server: Invalid argument. Check the server address and port.")
                        else:
                            print(f"Error connecting to the server: {e}")

            elif user_input.startswith('/register'):
                if not connected:
                    print("You must connect to a server first using /join <ip> <port>.")
                else:
                    try:
                        _, user_handle = user_input.split()
                        handle = user_handle
                        client_socket.send(user_input.encode('utf-8'))
                        response = client_socket.recv(BUFFER_SIZE)
                        print(response.decode('utf-8'))
                        registered = True
                    except ValueError:
                        print("Invalid command. Provide a handle for /register.")
                    except Exception as e:
                        print(f"An error occurred: {e}")

            elif user_input.startswith('/?'):
                display_help()

            elif connected:  # Check if the client is connected to a server
                if registered or user_input.startswith(('/leave', '/join', '/register', '/?')):
                    client_socket.send(user_input.encode('utf-8'))
                    if user_input.startswith('/store'):
                        filename = user_input.split()[1]
                        try:
                            with open(filename, 'rb') as file:
                                file_data = file.read()
                                client_socket.send(file_data)
                                print(f"File {filename} uploaded successfully.")
                        except FileNotFoundError:
                            print(f"File {filename} not found.")
                        except Exception as e:
                            print(f"Error uploading file: {e}")
                        except IndexError:
                            print("Invalid command. Provide a filename for /store.")
                        finally:
                            # Clear the buffer
                            received_data = b""
                    elif user_input.startswith('/get'):
                        filename = user_input.split()[1]
                        received_data = b""
                        try:
                            client_socket.send(user_input.encode('utf-8'))

                            response = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                            
                            received_data = b""

                            if response == "FILE_NOT_FOUND":
                                print(f"File {filename} not found on the server.")
                            else:
                                # Add padding if needed before decoding
                                padding = len(response) % 4
                                if padding:
                                    response += '=' * (4 - padding)
                                    # Decode base64 encoded data and write it to a file
                                file_data = base64.b64decode(response)
                                with open(filename, 'wb') as file:
                                    file.write(file_data)
                                    print(f"File {filename} downloaded successfully.")
                        except IndexError:
                            print("Invalid command. Provide a filename for /get.")
                        except Exception as e:
                            print(f"Error downloading file: {e}")
                        finally:
                            # Clear the buffer
                            received_data = b""

                    elif user_input.startswith('/dir'):
                        client_socket.send(user_input.encode('utf-8'))
                        received_data = b""
                        while True:
                            try:
                                chunk = client_socket.recv(BUFFER_SIZE)
                                received_data = b""
                                if not chunk:
                                    break  # Break the loop if no more data is received

                                received_data += chunk

                                if b"  " in received_data:
                                    print(received_data.decode('utf-8', errors='ignore').replace("      ", ""))
                                    received_data = received_data.split(b" ", 0)[0]
                                    break
                            except socket.timeout:
                                print("Error: Timeout occurred while receiving directory listing. The server may be unresponsive.")
                                break
                        # Clear the buffer
                        received_data = b""
                        try:
                            response = received_data.decode('utf-8')
                            if not response.strip():
                                print("   ")
                            else:
                                file_list = response.strip().split('\n')  # Split the received data using newline as the delimiter
                                print("Directory Listing:")
                                for filename in file_list:
                                    print(filename)
                        except UnicodeDecodeError as e:
                            print(f"Error decoding directory listing data: {e}")
                        finally:
                            # Clear the buffer
                            received_data = b""
                    else:
                        client_socket.send(user_input.encode('utf-8'))
                        response = client_socket.recv(BUFFER_SIZE)
                        print(response.decode('utf-8'))
                        # Clear the buffer
                        received_data = b""
                else:
                    print("You must register first before using this command.")
            else:
                print("You must connect to a server first using /join <ip> <port>.")
    except KeyboardInterrupt:
        print("Client shutting down.")
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        try:
            client_socket.close()
        except Exception as e:
            print(f"Error closing client socket: {e}")

if __name__ == "__main__":
    main()
