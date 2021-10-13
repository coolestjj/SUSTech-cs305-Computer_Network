# -*- coding: utf-8 -*-

# NOTE: you are NOT allowed to use the "requests" library in python in the assignment
from socket import *
import threading

# default IP and PORT
IP = '127.0.0.1'
PORT = 8080

def thread(ip, port):
    # Create a server socket
    tcpSerSock = socket(AF_INET, SOCK_STREAM)
    # bind it to the IP and Port,start listening and work
    # Fill in start.
    tcpSerSock.bind((ip, port))
    tcpSerSock.listen(10)
    # Fill in end.

    while 1:
        # Start receiving data from the client
        print('Ready to serve...')
        tcpCliSock, addr = tcpSerSock.accept()
        print('Received a connection from:', addr)
        # Proxy the request from the client
        # Fill in start.

        message = tcpCliSock.recv(4096).decode()
        # print(message)
        # message:
        # GET http://www.example.com/ HTTP/1.1
        # Host: www.example.com
        # User-Agent: curl/7.55.1
        # Accept: */*
        # Proxy-Connection: Keep-Alive

        filename = message.split()[1].partition("//")[2].partition('/')[0]
        # filename: www.example.com

        method = message.split()[0]

        try:
            file = open(filename)
            print('File exists in the cache')

            if method == 'GET' or method == 'HEAD':

                while True:
                    line = file.readline()
                    if 'Last-Modified' in line:
                        IMS = line.replace('Last-Modified', 'If-Modified-Since')
                        break

                IMS2 = IMS.encode()
                IMS2 = IMS2.replace(b'\n', b'\r\n\r\n')

                tcpHostSock = socket(AF_INET, SOCK_STREAM)

                host_name = message.split()[1].partition("//")[2].partition('/')[0]
                # host_name: www.example.com

                tcpHostSock.connect((host_name, 80))

                new_message = message.encode().replace(b'\r\n\r\n', b'\r\n' + IMS2)

                tcpHostSock.send(new_message)
                # b'GET http://www.example.com/ HTTP/1.1\r\nHost: www.example.com\r\nUser-Agent:......

                response = tcpHostSock.recv(4096)
                # b'HTTP/1.1 200 OK\r\nAccept-Ranges: bytes\r\nAge: 92037\r\nCache-Control:......

                if response.split()[1] == b'200':
                    print('Need to modify')
                    newFile = open('./' + filename, "w")
                    newFile.writelines(response.decode().replace('\r\n', '\n'))  # Send the response to client socket and the corresponding file in the cache
                    newFile.close()
                elif response.split()[1] == b'304':
                    print('No need to modify')

            file = open(filename)
            output_data = file.read()
            tcpCliSock.send(output_data.encode())

            print('Read from cache')

        # Cache file doesn't exist, so IOError
        except IOError:
            print('File does not exist in the cache')

            tcpHostSock = socket(AF_INET, SOCK_STREAM)

            host_name = message.split()[1].partition("//")[2].partition('/')[0]
            # host_name: www.example.com

            tcpHostSock.connect((host_name, 80))

            tcpHostSock.send(message.encode())
            # b'GET http://www.example.com/ HTTP/1.1\r\nHost: www.example.com\r\nUser-Agent:......

            response = tcpHostSock.recv(4096)
            # b'HTTP/1.1 200 OK\r\nAccept-Ranges: bytes\r\nAge: 92037\r\nCache-Control:......

            tcpCliSock.send(response)

            newFile = open(filename, "x")  # Create a new file in the cache for the requested file.
            newFile.writelines(response.decode().replace('\r\n', '\n'))  # Send the response to client socket and the corresponding file in the cache
            newFile.close()

        tcpCliSock.close()
        # Fill in end.


# Fill in start.
t = threading.Thread(target=thread, args=(IP, PORT))
t.start()
# Fill in end.
