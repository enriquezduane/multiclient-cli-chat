import socket
import threading

server_ip = "127.0.0.1" # localhost
port = 8000

def client_handler(client_socket):
    while True:
        request = client_socket.recv(1024).decode("utf-8")
        if request.lower() == "close":
            client_socket.send("closed".encode("utf-8"))
            break

        print(f"Received: {request}")

        response = request
        client_socket.send(response.encode("utf-8"))
    client_socket.close()
    pass

def run_server():
    # create a socket object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind server to socket
    print(f"Binding server to {server_ip}:{port}...")
    server.bind((server_ip, port))
    print("Server bound successfully.")

    # listen to incoming connections (0 means only one client can interact with server)
    server.listen(0)
    print(f"Listening on {server_ip}:{port}")


    while True:
        client_socket, client_address = server.accept()
        print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
        thread = threading.Thread(target=client_handler, args=(client_socket,))
        thread.start()


    print("Connection to client closed")
    # close server socket
    server.close()

run_server()
