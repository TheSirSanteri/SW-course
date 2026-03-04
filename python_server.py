import socket
import csv
import datetime

HOST = "10.225.28.206"
PORT = 5001

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

server_socket.settimeout(1.0)  # <-- tärkeä: accept() ei blokkaa ikuisesti

print(f"Listening for connections on port {PORT}...")

csv_filename = "./saving_data/training_sensor_data_1.csv"
with open(csv_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Sensor Value", "label"])

    client_socket = None
    try:
        # Odota yhteyttä (timeoutin takia loopissa)
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"Connected to {client_address}")
                client_socket.settimeout(1.0)  # <-- tärkeä: recv() ei blokkaa ikuisesti
                break
            except socket.timeout:
                pass  # jatka odottelua, Ctrl+C toimii tässä välissä

        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    print("Client disconnected.")
                    break

                text = data.decode("utf-8").strip()
                if text:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Received: {text}")
                    sensor_value = text.split(",")[0]
                    writer.writerow([timestamp, sensor_value, "pressed"])
                    file.flush()

            except socket.timeout:
                pass  # herää 1s välein -> Ctrl+C toimii

    except KeyboardInterrupt:
        print("Server stopped (Ctrl+C).")
    finally:
        if client_socket:
            client_socket.close()
        server_socket.close()