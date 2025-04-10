import socket
import threading
import os
import sys

def handle_client(connection, address):
    try:
        request = b""
        while b"\r\n\r\n" not in request:
            request += connection.recv(1024)

        request_lines = request.decode("utf-8").split("\r\n")
        print("Received request:")
        print(request.decode("utf-8"))

        if not request_lines:
            connection.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        request_line = request_lines[0]
        parts = request_line.split()

        if len(parts) < 2:
            connection.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        method, path = parts[0], parts[1]

        headers = {}
        for line in request_lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        body = b""
        if "content-length" in headers:
            content_length = int(headers["content-length"])
            while len(body) < content_length:
                body += connection.recv(1024)

        if path == "/":
            response = b"HTTP/1.1 200 OK\r\n\r\n"

        elif path.startswith("/echo/"):
            value = path[len("/echo/"):]
            response_body = value.encode()
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                + b"Content-Length: " + str(len(response_body)).encode() + b"\r\n\r\n"
                + response_body
            )

        elif path == "/user-agent":
            user_agent = headers.get("user-agent", "")
            response_body = user_agent.encode()
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                + b"Content-Length: " + str(len(response_body)).encode() + b"\r\n\r\n"
                + response_body
            )

        elif path.startswith("/files/"):
            directory = sys.argv[2]
            filename = path[len("/files/"):]
            filepath = os.path.join(directory, filename)

            if method == "GET":
                try:
                    if os.path.isfile(filepath):
                        with open(filepath, "rb") as f:
                            file_data = f.read()
                        response = (
                            b"HTTP/1.1 200 OK\r\n"
                            b"Content-Type: application/octet-stream\r\n"
                            + b"Content-Length: " + str(len(file_data)).encode() + b"\r\n\r\n"
                            + file_data
                        )
                    else:
                        response = b"HTTP/1.1 404 Not Found\r\n\r\n"
                except Exception:
                    response = b"HTTP/1.1 500 Internal Server Error\r\n\r\n"

            elif method == "POST":
                try:
                    with open(filepath, "wb") as f:
                        f.write(body)
                    response = b"HTTP/1.1 201 Created\r\n\r\n"
                except Exception:
                    response = b"HTTP/1.1 500 Internal Server Error\r\n\r\n"
            else:
                response = b"HTTP/1.1 405 Method Not Allowed\r\n\r\n"

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
