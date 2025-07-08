import socket

server_ip = "127.0.0.1" # localhost
port = 8000

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

    client_socket, client_address = server.accept()
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

    while True:
        request = client_socket.recv(1024)
        request = request.decode("utf-8")

        if request.lower() == "close":
            client_socket.send("closed".encode("utf-8"))
            break

        print(f"Received: {request}")

    client_socket.close()
    print("Connection to client closed")
    # close server socket
    server.close()

run_server()
