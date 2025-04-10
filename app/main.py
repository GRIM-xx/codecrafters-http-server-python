import socket
import threading
import os
import sys
import gzip
import io

# Constants
STATUS_200 = b"HTTP/1.1 200 OK\r\n"
STATUS_201 = b"HTTP/1.1 201 Created\r\n\r\n"
STATUS_400 = b"HTTP/1.1 400 Bad Request\r\n\r\n"
STATUS_404 = b"HTTP/1.1 404 Not Found\r\n\r\n"
STATUS_500 = b"HTTP/1.1 500 Internal Server Error\r\n\r\n"

def compress_gzip(data: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb") as gzip_file:
        gzip_file.write(data)
    return buffer.getvalue()

def parse_headers(header_lines):
    headers = {}
    for line in header_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    return headers

def handle_client(connection, address):
    try:
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = connection.recv(1024)
            if not chunk:
                break
            request += chunk

        header_part, _, body = request.partition(b"\r\n\r\n")
        header_lines = header_part.decode().split("\r\n")
        if not header_lines:
            connection.sendall(STATUS_400)
            return

        print("Received request:")
        print(header_part.decode())
        print(body.decode(errors="ignore"))

        request_line = header_lines[0].split()
        if len(request_line) < 2:
            connection.sendall(STATUS_400)
            return

        method, path = request_line[0], request_line[1]
        headers = parse_headers(header_lines[1:])

        accept_encoding = headers.get("accept-encoding", "")
        content_length = int(headers.get("content-length", "0"))
        while len(body) < content_length:
            chunk = connection.recv(1024)
            if not chunk:
                break
            body += chunk

        response_body = b""
        content_type = b"text/plain"
        should_compress = "gzip" in accept_encoding.lower()

        if path == "/":
            connection.sendall(STATUS_200 + b"\r\n")
            return

        elif path.startswith("/echo/"):
            response_body = path[len("/echo/"):].encode()

        elif path == "/user-agent":
            response_body = headers.get("user-agent", "").encode()

        elif path.startswith("/files/"):
            directory = sys.argv[2]
            filename = path[len("/files/"):]
            filepath = os.path.join(directory, filename)

            if method == "GET":
                if os.path.isfile(filepath):
                    with open(filepath, "rb") as f:
                        response_body = f.read()
                    content_type = b"application/octet-stream"
                else:
                    connection.sendall(STATUS_404)
                    return

            elif method == "POST":
                try:
                    with open(filepath, "wb") as f:
                        f.write(body)
                    connection.sendall(STATUS_201)
                    return
                except Exception:
                    connection.sendall(STATUS_500)
                    return
        else:
            connection.sendall(STATUS_404)
            return

        if should_compress:
            response_body = compress_gzip(response_body)
            content_encoding_header = b"Content-Encoding: gzip\r\n"
        else:
            content_encoding_header = b""

        response_headers = (
            STATUS_200 +
            b"Content-Type: " + content_type + b"\r\n" +
            b"Content-Length: " + str(len(response_body)).encode() + b"\r\n" +
            content_encoding_header +
            b"\r\n"
        )
        connection.sendall(response_headers + response_body)

    finally:
        connection.close()

def main():
    print("Starting the server ...")
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    main()
