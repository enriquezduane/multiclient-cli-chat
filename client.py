import socket

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8000

def run_client():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((SERVER_IP, SERVER_PORT))
            print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

            while True:
                msg = input("Enter message (or 'exit' to quit): ")

                client.send(msg.encode("utf-8"))

                if msg.lower() == "exit":
                    print("Exit command sent. Closing client.")
                    break

                response_bytes = client.recv(1024)

                if not response_bytes:
                    print("Server has closed the connection.")
                    break

                response = response_bytes.decode("utf-8")
                print(f"Received: {response}")

    except ConnectionRefusedError:
        print(f"Connection to {SERVER_IP}:{SERVER_PORT} was refused. Is the server running?")
    except ConnectionResetError:
        print("Connection to the server was lost.")
    except BrokenPipeError:
        print("The connection pipe is broken. The server may have quit unexpectedly.")
    except KeyboardInterrupt:
        print("\nClient shutting down.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Connection closed.")

run_client()
