import socket
import threading
import sys
import struct
import time
import signal

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8000

# Global flag for graceful shutdown
client_running = True
client_socket = None

def send_message(sock, message):
    """Send a message with length prefix to handle partial reception"""
    try:
        message_bytes = message.encode("utf-8")
        message_length = len(message_bytes)
        # Send 4-byte length prefix followed by message
        length_prefix = struct.pack('!I', message_length)
        sock.sendall(length_prefix + message_bytes)
        return True
    except (socket.error, ConnectionResetError, BrokenPipeError):
        return False

def receive_message(sock):
    """Receive a message with length prefix to handle partial reception"""
    try:
        # First receive the 4-byte length prefix
        length_data = b''
        while len(length_data) < 4:
            chunk = sock.recv(4 - len(length_data))
            if not chunk:
                return None
            length_data += chunk
        
        message_length = struct.unpack('!I', length_data)[0]
        
        # Validate message length to prevent memory issues
        if message_length > 10000:  # 10KB limit
            return None
            
        # Now receive the actual message
        message_data = b''
        while len(message_data) < message_length:
            chunk = sock.recv(message_length - len(message_data))
            if not chunk:
                return None
            message_data += chunk
            
        return message_data.decode("utf-8")
    except (socket.error, ConnectionResetError, UnicodeDecodeError, struct.error):
        return None

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global client_running
    print("\nShutting down client...")
    client_running = False
    if client_socket:
        try:
            send_message(client_socket, "exit")
            client_socket.close()
        except:
            pass
    sys.exit(0)

def receive_handler(sock):
    """Handle incoming messages from server"""
    global client_running
    
    while client_running:
        try:
            response = receive_message(sock)
            
            if not response:
                if client_running:
                    print("\nServer has closed the connection.")
                break
            
            # Check for server messages
            if response.startswith("ERROR:"):
                print(f"\n{response}")
                continue
            elif response.startswith("SERVER:"):
                print(f"\n{response}")
                if "shutting down" in response.lower():
                    client_running = False
                    break
                continue
            elif response.startswith("[PRIVATE"):
                # Highlight private messages
                print(f"\n🔒 {response}")
                if client_running:
                    sys.stdout.write("You: ")
                    sys.stdout.flush()
                continue
            elif response.startswith("Connected users"):
                # Format user list nicely
                print(f"\n👥 {response}")
                if client_running:
                    sys.stdout.write("You: ")
                    sys.stdout.flush()
                continue
            elif response.startswith("Available commands:"):
                # Format help text nicely
                print(f"\n📋 Help:")
                print(response)
                if client_running:
                    sys.stdout.write("You: ")
                    sys.stdout.flush()
                continue
            
            # Clear current input line and display message
            sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
            sys.stdout.write(f"{response}\n")
            if client_running:
                sys.stdout.write("You: ")
                sys.stdout.flush()

        except Exception as e:
            if client_running:
                print(f"\nAn error occurred while receiving: {e}")
            break
    
    client_running = False

def input_handler(sock):
    """Handle user input in a separate thread"""
    global client_running
    
    while client_running:
        try:
            if not client_running:
                break
                
            msg = input("You: ")
            
            if not client_running:
                break
                
            if not msg.strip():
                continue
            
            # Show helpful hints for commands
            if msg.strip() == "/":
                print("💡 Tip: Type /help to see available commands")
                continue
                
            # Validate message length
            if len(msg) > 1000:
                print("Message too long. Maximum 1000 characters allowed.")
                continue
                
            if not send_message(sock, msg):
                print("Failed to send message. Connection may be lost.")
                client_running = False
                break

            if msg.lower() == "exit":
                print("Exit command sent. Closing client.")
                client_running = False
                break
                
        except EOFError:
            # Handle Ctrl+D
            print("\nReceived EOF. Exiting...")
            client_running = False
            break
        except KeyboardInterrupt:
            # This will be handled by signal handler
            break
        except Exception as e:
            if client_running:
                print(f"Error reading input: {e}")
            break

def validate_username(username):
    """Validate username input"""
    if not username or not username.strip():
        return False, "Username cannot be empty"
    
    username = username.strip()
    if len(username) > 50:
        return False, "Username too long (max 50 characters)"
    
    # Check for invalid characters
    invalid_chars = ['[', ']', ':', '\n', '\r', '\t']
    if any(char in username for char in invalid_chars):
        return False, "Username contains invalid characters"
    
    return True, username

def run_client():
    """Run the chat client"""
    global client_running, client_socket
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"Connecting to server at {SERVER_IP}:{SERVER_PORT}...")
        client_socket.settimeout(10.0)  # 10 second connection timeout
        client_socket.connect((SERVER_IP, SERVER_PORT))
        client_socket.settimeout(None)  # Remove timeout after connection
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

        # Get and validate username
        while True:
            try:
                username = input("Enter your username: ")
                valid, result = validate_username(username)
                if valid:
                    username = result
                    break
                else:
                    print(f"Invalid username: {result}")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                return

        # Send username to server
        if not send_message(client_socket, username):
            print("Failed to send username to server.")
            return

        print(f"Joined chat as: {username}")
        print("💬 Chat Commands:")
        print("   • Type messages normally to chat with everyone")
        print("   • /whisper <user> <message> - Send private message")
        print("   • /who - List all users")
        print("   • /help - Show all commands")
        print("   • 'exit' or Ctrl+C - Leave chat")
        print("-" * 50)

        # Start receiver thread
        receiver_thread = threading.Thread(target=receive_handler, args=(client_socket,), daemon=True)
        receiver_thread.start()

        # Start input handler in main thread
        input_handler(client_socket)

        # Wait a moment for any final messages
        if receiver_thread.is_alive():
            receiver_thread.join(timeout=2.0)

    except socket.timeout:
        print(f"Connection to {SERVER_IP}:{SERVER_PORT} timed out. Is the server running?")
    except ConnectionRefusedError:
        print(f"Connection to {SERVER_IP}:{SERVER_PORT} was refused. Is the server running?")
    except ConnectionResetError:
        print("Connection to the server was lost.")
    except BrokenPipeError:
        print("The connection pipe is broken. The server may have quit unexpectedly.")
    except OSError as e:
        print(f"Network error: {e}")
    except KeyboardInterrupt:
        print("\nClient shutting down.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        client_running = False
        if client_socket:
            try:
                client_socket.close()
            except:
                pass
        print("Connection closed.")

if __name__ == "__main__":
    run_client()
