import socket
import threading

server_ip = "127.0.0.1" # localhost
port = 8000

clients = {}
clients_lock = threading.Lock()

def broadcast(message, sender_socket=None):
    with clients_lock:
        for client_socket in list(clients.keys()):
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode("utf-8"))
                except socket.error:
                    print(f"Failed to send message to {clients.get(client_socket, 'unknown')}. Connection may be lost.")

def client_handler(client_socket, client_address):
    username = None
    try:
        username = client_socket.recv(1024).decode("utf-8").strip()
        if not username:
            username = f"User_{client_address[1]}"
            
        with clients_lock:
            clients[client_socket] = username
            
        join_msg = f"--- {username} has joined the chat ---"
        broadcast(join_msg)
        
        while True:
            request = client_socket.recv(1024).decode("utf-8")
            if request.lower() in ["close", "exit"] or not request:
                if request.lower() in ["close", "exit"]:
                    client_socket.send("closed".encode("utf-8"))
                break
                
            broadcast_msg = f"[{username}]: {request}"
            print(f"Broadcasting from {username}: {request}")
            broadcast(broadcast_msg, client_socket)
            
    except (ConnectionResetError, ConnectionAbortedError):
        print(f"Connection reset by {client_address}.")
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        with clients_lock:
            if client_socket in clients:
                if username:
                    leave_msg = f"--- {username} has left the chat ---"
                    broadcast(leave_msg)
                del clients[client_socket]
        client_socket.close()
        print(f"Connection to {client_address} closed.")

def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        print(f"Binding server to {server_ip}:{port}...")
        server.bind((server_ip, port))
        print("Server bound successfully.")

        server.listen(5)
        print(f"Listening on {server_ip}:{port}")

        while True:
            client_socket, client_address = server.accept()
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            thread = threading.Thread(
                target=client_handler, args=(client_socket, client_address)
            )
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server.close()
        print("Server closed.")

run_server()
