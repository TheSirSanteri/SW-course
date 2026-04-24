import socket
import time

ESP32_HOST = "0.0.0.0"
ESP32_PORT = 5001

LOCAL_SERVER = "127.0.0.1"
LOCAL_PORT = 6000

"""
Sensors:

Fingers (lower voltage means more bent):
D0 - thumb
D1 - index
D2 - middle
D3 - ring
D4 - pinky

pressure sensors (lower voltage means more pressure):
D5 - thumb
D8 - index
D9 - middle
D10 - ring
"""


def connect_to_local_processor():
    while True:
        try:
            localSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            localSocket.connect((LOCAL_SERVER, LOCAL_PORT))
            print(f"Connected to local server at {LOCAL_SERVER}:{LOCAL_PORT}")
            return localSocket
        except ConnectionRefusedError:
            print("Waiting for local server...")
            time.sleep(1)

def main():
    forward_socket = connect_to_local_processor()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ESP32_HOST, ESP32_PORT))
    server_socket.listen(1)
    server_socket.settimeout(1.0)

    print(f"Listening for ESP32 on {ESP32_HOST}:{ESP32_PORT}")

    client_socket = None

    try:
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"ESP32 connected from {client_address}")
                client_socket.settimeout(1.0)

                buffer = ""

                while True:
                    try:
                        data = client_socket.recv(1024)
                        if not data:
                            print("ESP32 disconnected.")
                            break

                        buffer += data.decode("utf-8")

                        # handle multiple lines in the buffer
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue

                            print(f"Received from ESP32: {line}")

                            message = line + "\n"

                            #Error handling
                            try:
                                forward_socket.sendall(message.encode("utf-8"))
                            except (BrokenPipeError, ConnectionResetError):
                                print("Local server disconnected. Reconnecting...")
                                forward_socket.close()
                                forward_socket = connect_to_local_processor()
                                forward_socket.sendall(message.encode("utf-8"))

                    except socket.timeout:
                        continue

            except socket.timeout:
                continue

            finally:
                if client_socket:
                    client_socket.close()
                    client_socket = None

    except KeyboardInterrupt:
        print("Receiver stopped.")

    finally:
        if client_socket:
            client_socket.close()
        forward_socket.close()
        server_socket.close()


if __name__ == "__main__":
    main()


