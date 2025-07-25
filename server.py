import socket
import threading
import struct
import time

server_ip = "127.0.0.1" # localhost
port = 8000

clients = {}
clients_lock = threading.Lock()
server_running = True

def send_message(client_socket, message):
    """Send a message with length prefix to handle partial reception"""
    try:
        message_bytes = message.encode("utf-8")
        message_length = len(message_bytes)
        # Send 4-byte length prefix followed by message
        length_prefix = struct.pack('!I', message_length)
        client_socket.sendall(length_prefix + message_bytes)
        return True
    except (socket.error, ConnectionResetError, BrokenPipeError):
        return False

def receive_message(client_socket):
    """Receive a message with length prefix to handle partial reception"""
    try:
        # First receive the 4-byte length prefix
        length_data = b''
        while len(length_data) < 4:
            chunk = client_socket.recv(4 - len(length_data))
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
            chunk = client_socket.recv(message_length - len(message_data))
            if not chunk:
                return None
            message_data += chunk
            
        return message_data.decode("utf-8")
    except (socket.error, ConnectionResetError, UnicodeDecodeError, struct.error):
        return None

def broadcast(message, sender_socket=None):
    """Broadcast message to all clients except sender"""
    disconnected_clients = []
    
    with clients_lock:
        # Create a copy of clients to avoid modification during iteration
        clients_copy = dict(clients)
    
    for client_socket, username in clients_copy.items():
        if client_socket != sender_socket:
            if not send_message(client_socket, message):
                print(f"Failed to send message to {username}. Marking for removal.")
                disconnected_clients.append(client_socket)
    
    # Remove disconnected clients
    if disconnected_clients:
        with clients_lock:
            for client_socket in disconnected_clients:
                if client_socket in clients:
                    username = clients[client_socket]
                    del clients[client_socket]
                    print(f"Removed disconnected client: {username}")
                try:
                    client_socket.close()
                except:
                    pass

def send_private_message(sender_username, target_username, message):
    """Send a private message to a specific user"""
    target_socket = None
    
    with clients_lock:
        # Find the target user's socket
        for socket, username in clients.items():
            if username.lower() == target_username.lower():
                target_socket = socket
                break
    
    if target_socket:
        private_msg = f"[PRIVATE from {sender_username}]: {message}"
        if send_message(target_socket, private_msg):
            return True, f"Private message sent to {target_username}"
        else:
            return False, f"Failed to send message to {target_username} (connection issue)"
    else:
        return False, f"User '{target_username}' not found"

def get_user_list():
    """Get a list of all connected users"""
    with clients_lock:
        usernames = list(clients.values())
    
    if usernames:
        user_list = "Connected users (" + str(len(usernames)) + "): " + ", ".join(sorted(usernames))
    else:
        user_list = "No users currently connected"
    
    return user_list

def handle_command(client_socket, username, message):
    """Handle chat commands starting with /"""
    parts = message.strip().split()
    command = parts[0].lower()
    
    if command == "/whisper" or command == "/w":
        if len(parts) < 3:
            send_message(client_socket, "ERROR: Usage: /whisper <username> <message>")
            return
        
        target_username = parts[1]
        whisper_message = " ".join(parts[2:])
        
        success, response = send_private_message(username, target_username, whisper_message)
        
        if success:
            # Send confirmation to sender
            confirmation = f"[PRIVATE to {target_username}]: {whisper_message}"
            send_message(client_socket, confirmation)
        else:
            send_message(client_socket, f"ERROR: {response}")
    
    elif command == "/who" or command == "/users":
        user_list = get_user_list()
        send_message(client_socket, user_list)
    
    elif command == "/help" or command == "/h":
        help_text = """Available commands:
/whisper <username> <message> (or /w) - Send a private message
/who (or /users) - List all connected users  
/help (or /h) - Show this help message
/exit - Leave the chat"""
        send_message(client_socket, help_text)
    
    else:
        send_message(client_socket, f"ERROR: Unknown command '{command}'. Type /help for available commands.")

def client_handler(client_socket, client_address):
    """Handle individual client connections"""
    username = None
    try:
        # Set socket timeout for operations
        client_socket.settimeout(30.0)
        
        # Receive username with proper message framing
        username = receive_message(client_socket)
        if not username:
            print(f"Failed to receive username from {client_address}")
            return
            
        username = username.strip()
        
        # Validate username
        if not username or len(username) > 50:
            send_message(client_socket, "ERROR: Invalid username")
            return
            
        # Check for duplicate usernames
        with clients_lock:
            existing_usernames = set(clients.values())
            if username in existing_usernames:
                counter = 1
                original_username = username
                while username in existing_usernames:
                    username = f"{original_username}_{counter}"
                    counter += 1
            
            clients[client_socket] = username
            
        join_msg = f"--- {username} has joined the chat ---"
        print(f"User {username} joined from {client_address}")
        broadcast(join_msg)
        
        # Send welcome message to the user
        welcome_msg = f"""Welcome to the chat, {username}!
Type /help to see available commands.
Current users: {len(clients)}"""
        send_message(client_socket, welcome_msg)
        
        # Remove timeout for message receiving
        client_socket.settimeout(None)
        
        while server_running:
            request = receive_message(client_socket)
            if not request:
                break
                
            if request.lower() in ["close", "exit"]:
                send_message(client_socket, "Goodbye!")
                break
                
            # Validate message length
            if len(request) > 1000:  # 1KB message limit
                send_message(client_socket, "ERROR: Message too long")
                continue
            
            # Check if it's a command
            if request.startswith('/'):
                handle_command(client_socket, username, request)
            else:
                # Regular broadcast message
                broadcast_msg = f"[{username}]: {request}"
                print(f"Broadcasting from {username}: {request}")
                broadcast(broadcast_msg, client_socket)
            
    except socket.timeout:
        print(f"Client {client_address} timed out during initial handshake.")
    except (ConnectionResetError, ConnectionAbortedError):
        print(f"Connection reset by {client_address}.")
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        # Clean up client
        with clients_lock:
            if client_socket in clients:
                if username:
                    leave_msg = f"--- {username} has left the chat ---"
                    print(f"User {username} left")
                    broadcast(leave_msg)
                del clients[client_socket]
        
        try:
            client_socket.close()
        except:
            pass
        print(f"Connection to {client_address} closed.")

def shutdown_server():
    """Gracefully shutdown the server"""
    global server_running
    server_running = False
    
    print("Shutting down server gracefully...")
    
    # Notify all clients and close connections
    with clients_lock:
        clients_copy = dict(clients)
    
    for client_socket, username in clients_copy.items():
        try:
            send_message(client_socket, "SERVER: Server is shutting down. Goodbye!")
            client_socket.close()
        except:
            pass
    
    with clients_lock:
        clients.clear()

def run_server():
    """Run the chat server"""
    global server_running
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        print(f"Binding server to {server_ip}:{port}...")
        server.bind((server_ip, port))
        print("Server bound successfully.")

        server.listen(5)
        print(f"Listening on {server_ip}:{port}")
        print("Server is ready to accept connections. Press Ctrl+C to stop.")

        while server_running:
            try:
                server.settimeout(1.0)  # Allow periodic checks for shutdown
                client_socket, client_address = server.accept()
                
                if not server_running:
                    client_socket.close()
                    break
                    
                print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
                thread = threading.Thread(
                    target=client_handler, 
                    args=(client_socket, client_address),
                    daemon=True
                )
                thread.start()
                
            except socket.timeout:
                continue  # Check if server should keep running
            except OSError:
                if server_running:
                    print("Error accepting connections")
                break
                
    except KeyboardInterrupt:
        print("\nReceived shutdown signal.")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        shutdown_server()
        server.close()
        print("Server closed.")

if __name__ == "__main__":
    run_server()
