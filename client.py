import socket
import threading
import sys # Import sys for better printing

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8000

def receive_handler(client_socket):
    while True:
        try:
            response_bytes = client_socket.recv(1024)

            if not response_bytes:
                print("\nServer has closed the connection. Press Enter to exit.")
                break
            
            response = response_bytes.decode("utf-8")

            sys.stdout.write(f"\r{response}\n")
            sys.stdout.write("You: ")
            sys.stdout.flush()


        except ConnectionResetError:
            print("\nConnection to the server was lost. Press Enter to exit.")
            break
        except Exception as e:
            print(f"\nAn error occurred while receiving: {e}. Press Enter to exit.")
            break

def run_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

        username = input("Enter your username: ")
        client.send(username.encode("utf-8"))

        receiver_thread = threading.Thread(target=receive_handler, args=(client,))
        receiver_thread.daemon = True
        receiver_thread.start()

        while True:
            msg = input("You: ")

            client.send(msg.encode("utf-8"))

            if msg.lower() == "exit":
                print("Exit command sent. Closing client.")
                break

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
        client.close()

if __name__ == "__main__":
    run_client()
