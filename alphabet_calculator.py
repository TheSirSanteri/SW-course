import socket
import sys
from collections import deque

HOST = "127.0.0.1"
PORT = 6000

PIN_NAMES = ["D0", "D1", "D2", "D3", "D4", "D5", "D8", "D9", "D10"]
EXPECTED_VALUES = len(PIN_NAMES)
ADC_MAX = 4095.0
REFERENCE_VOLTAGE = 3.3

def adc_to_voltage(raw_value: float) -> float:
    return (raw_value / ADC_MAX) * REFERENCE_VOLTAGE


def parse_sensor_line(line: str):
    parts = [part.strip() for part in line.split(",")]

    if len(parts) != EXPECTED_VALUES:
        raise ValueError(f"Expected {EXPECTED_VALUES} values, got {len(parts)}")

    raw_values = [float(part) for part in parts]
    return [adc_to_voltage(value) for value in raw_values]


def print_voltages_inline(voltages):
    formatted = " ; ".join(f"{voltage:.2f}" for voltage in voltages) + " ;"
    # Tyhjennetään aiempi rivi ja kirjoitetaan uusi samalle riville
    sys.stdout.write("\r" + " " * 120 + "\r")
    sys.stdout.write(formatted)
    sys.stdout.flush()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    print(f"Realtime processor listening on {HOST}:{PORT}")
    print("Jännitteet")

    client_socket, client_address = server_socket.accept()
    print(f"Local sender connected from {client_address}")

    buffer = ""

    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                print("\nSender disconnected.")
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()

                if not line:
                    continue

                try:
                    voltages = parse_sensor_line(line)
                    print_voltages_inline(voltages)
                except ValueError as e:
                    sys.stdout.write("\n")
                    print(f"Virhe rivissä: {line}")
                    print(f"Syy: {e}")
                    print("Jännitteet")

    except KeyboardInterrupt:
        print("\nProcessor stopped.")

    finally:
        client_socket.close()
        server_socket.close()


if __name__ == "__main__":
    main()
