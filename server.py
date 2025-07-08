import socket
import threading

server_ip = "127.0.0.1" # localhost
port = 8000

def client_handler(client_socket, client_address):
    try:
        while True:
            request = client_socket.recv(1024).decode("utf-8")
            if request.lower() == "close":
                client_socket.send("closed".encode("utf-8"))
                break
            elif not request:
                print(f"Client {client_address} disconnected.")
                break

            print(f"Received from {client_address}: {request}")

            response = request
            client_socket.send(response.encode("utf-8"))
    except ConnectionResetError:
        print(f"Connection reset by {client_address}.")
    finally:
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
