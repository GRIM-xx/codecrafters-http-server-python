import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    # server_socket.accept() # wait for client

    while True:
        connection, address = server_socket.accept()
        request = connection.recv(1024).decode("utf-8")
        print("Received request:")
        print(request)

        request_lines = request.splitlines()
        if not request_lines:
            connection.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            connection.close()
            continue

        request_line = request_lines[0]
        parts = request_line.split()

        if len(parts) < 2:
            connection.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            connection.close()
            continue

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
        else:
            response = b"HTTP/1.1 404 Not Found\r\n\r\n"

        connection.sendall(response)
        connection.close()

if __name__ == "__main__":
    main()
