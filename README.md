# Multi-Client Command-Line Chat.

python m venv .venv

source activate

no dependencies needed. socket library is built in

inet is ipv4
stream is tcp sockets

socket = ipadd:port

ex. 127.0.0.1:80

for setting ports in a server, use values above 1023 to avoid collission with other system ports

bind just assigns an IP:port to a socket. not ready for connections yet

listen queues for incoming connections

accept takes a connection from the listen queue and returns socket object and address

socket object is used by the server to communicate (send and receive messages or data) to client

you cannot predict how many bytes each recv returns

ephemeral port - auto assigned port (this happens when client connects to server)

to implement multithreading, use threading
