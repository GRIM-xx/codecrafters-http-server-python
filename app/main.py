import socket
import threading
import os
import sys

def handle_client(connection, address):
    try:
        request = connection.recv(1024).decode("utf-8")
        print("Received request:")
        print(request)

        request_lines = request.splitlines()
        if not request_lines:
            connection.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        request_line = request_lines[0]
        parts = request_line.split()

        if len(parts) < 2:
            connection.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        method, path = parts[0], parts[1]

        if path == "/":
            response = b"HTTP/1.1 200 OK\r\n\r\n"

        elif path.startswith("/echo/"):
            value = path[len("/echo/"):]
            body = value.encode()
            headers = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n"
            response = headers + body

        elif path == "/user-agent":
            user_agent = ""
            for line in request_lines[1:]:
                if line.lower().startswith("user-agent:"):
                    user_agent = line[len("User-Agent:"):].strip()
                    break

            body = user_agent.encode()
            headers = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n"
            response = headers + body

        elif path.startswith("/files/"):
            directory = sys.argv[2]
            filename = path[len("/files/"):]
            filepath = os.path.join(directory, filename)

            if method == "GET":
                try:
                    if os.path.isfile(filepath):
                        with open(filepath, "rb") as f:
                            body = f.read()
                        headers = b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n"
                        response = headers + body
                except Exception as e:
                    response = b"HTTP/1.1 404 Not Found\r\n\r\n"

            elif method == "POST":
                content_length = 0
                for line in request_lines:
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":")[1].strip())
                        break

                body = connection.recv(content_length)

                try:
                    with open(filepath, "wb") as f:
                        f.write(body)
                    response = b"HTTP/1.1 201 Created\r\n\r\n"
                except Exception as e:
                    print(f"Error writing file {filepath}: {e}")
                    response = b"HTTP/1.1 500 Internal Server Error\r\n\r\n"

        else:
            response = b"HTTP/1.1 404 Not Found\r\n\r\n"

        connection.sendall(response)
    finally:
        connection.close()

def main():
    print("Starting the server ...")
    
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        connection, address = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(connection, address))
        thread.start()

if __name__ == "__main__":
    main()
