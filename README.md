# Multi-Client Command-Line Chat

![Project GIF](https://github.com/user-attachments/assets/4d70abb2-0132-4ace-89b1-fad143a2ef96)

### Motivation

This project was created to build a functional, real-time chat application that runs in the command line. The goal was to implement a robust client-server architecture that allows multiple users to connect and communicate simultaneously, while also providing features like private messaging and user lists.

### Tech Stack

*   **Python 3**
*   **socket**: For low-level network communication (TCP sockets).
*   **threading**: To handle multiple client connections concurrently.
*   **struct**: To ensure reliable message delivery by packing and unpacking message lengths.
*   **signal**: For graceful server and client shutdown on interruption.

### Installation

No external dependencies are required to run this project. All necessary libraries are part of the standard Python library.

**1. Start the Server**

Open a terminal and run the following command to start the chat server. It will listen for incoming connections.

```bash
python3 server.py
```

**2. Run the Client**

Open one or more new terminal windows to run the client application. Each instance will connect to the server.

```bash
python3 client.py
```

You will be prompted to enter a username. Once connected, you can start chatting with other users.

### What I Learned

This project was a deep dive into several key programming concepts:

*   I learned how to establish a **client-server connection** using Python's `socket` library. This involved understanding the difference between **IPv4 (`AF_INET`)** and **TCP (`SOCK_STREAM`)**, and correctly using methods like `bind()`, `listen()`, and `accept()` on the server to manage incoming connections.

*    A critical challenge was ensuring that messages are received completely. I implemented a **protocol** where each message is prefixed with its length using `struct.pack`. The receiver then reads this prefix first to know exactly how many bytes to expect, preventing errors from partial `socket.recv()` calls.

*   To handle multiple clients at once without blocking, I used the `threading` library. Each client is managed in a **separate thread** on the server. I also learned the importance of using `threading.Lock` to prevent **race conditions** when accessing shared data, such as the dictionary of connected clients.

*   I implemented mechanisms for a **graceful exit**. Using `try...except` blocks and the `signal` library to catch `KeyboardInterrupt` (Ctrl+C), the server and client can shut down cleanly, close their sockets, and notify other users of their departure.

*   The client-side code focuses on creating a smooth user experience in the terminal. This includes handling user input in a non-blocking way, clearing lines to display new messages, and implementing a simple **command parser** for features like `/whisper`, `/who`, and `/help`.
