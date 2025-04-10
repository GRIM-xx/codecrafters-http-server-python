import socket
import threading
import os
import sys

def get_directory():
    if "--directory" not in sys.argv:
        print("Error: --directory flag is missing.")
        sys.exit(1)

    directory_index = sys.argv.index("--directory") + 1
    if directory_index < len(sys.argv):
        directory = sys.argv[directory_index]
        if not os.path.isabs(directory):
            print("Error: The directory path must be an absolute path.")
            sys.exit(1)
        return directory
    else:
        print("Error: No directory path provided after --directory.")
        sys.exit(1)


FILES_DIR = get_directory()

def handle_client(connection):
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

        elif path.startswith("/files/") and method == "GET":
            filename = path[len("/files/"):]
            filepath = os.path.join(FILES_DIR, filename)

            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    body = f.read()
                headers = b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n"
                response = headers + body
            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"

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
        thread = threading.Thread(target=handle_client, args=(connection,))
        thread.start()

if __name__ == "__main__":
    main()
