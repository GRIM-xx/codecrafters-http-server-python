import socket
import threading
import os
import sys
import gzip
import io

def compress_response(body: bytes, encoding: str):
    if encoding == "gzip":
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as gzip_file:
            gzip_file.write(body)
        return buf.getvalue(), "gzip"
    return body, None

def handle_client(connection, address):
    try:
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = connection.recv(1024)
            if not chunk:
                break
            request += chunk

        header_part, _, body = request.partition(b"\r\n\r\n")
        request_lines = header_part.decode("utf-8").split("\r\n")

        print("Received request:")
        print(header_part.decode("utf-8"))
        print(body.decode("utf-8", errors="ignore"))

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

        accept_encoding = headers.get("accept-encoding", "")
        content_length = int(headers.get("content-length", 0))

        while len(body) < content_length:
            chunk = connection.recv(1024)
            if not chunk:
                break
            body += chunk

        response_body = b""
        content_type = b"text/plain"
        content_encoding_header = b""

        if path == "/":
            response = b"HTTP/1.1 200 OK\r\n\r\n"

        elif path.startswith("/echo/"):
            value = path[len("/echo/"):]
            response_body = value.encode()

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
                    connection.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                    return
            elif method == "POST":
                try:
                    with open(filepath, "wb") as f:
                        f.write(body)
                    connection.sendall(b"HTTP/1.1 201 Created\r\n\r\n")
                    return
                except Exception:
                    connection.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
                    return

        else:
            connection.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
            return

        if "gzip" in accept_encoding.lower():
            response_body, encoding_used = compress_response(response_body, "gzip")
            content_encoding_header = b"Content-Encoding: gzip\r\n"

        response_headers = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: " + content_type + b"\r\n"
            + b"Content-Length: " + str(len(response_body)).encode() + b"\r\n"
            + content_encoding_header +
            b"\r\n"
        )

        connection.sendall(response_headers + response_body)

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
