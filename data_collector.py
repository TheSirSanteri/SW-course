import csv
import socket
import threading
import time
from pathlib import Path

HOST = "127.0.0.1"
PORT = 6000

PIN_NAMES = ["A0", "A1", "A2", "A3", "A4", "D7", "D8", "D9", "D10"]
EXPECTED_VALUES = len(PIN_NAMES)

ADC_MAX = 4095.0
REFERENCE_VOLTAGE = 3.3

OUTPUT_DIR = Path("./datasets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def adc_to_voltage(raw_value: float) -> float:
    return (raw_value / ADC_MAX) * REFERENCE_VOLTAGE


def parse_sensor_line(line: str):
    parts = [part.strip() for part in line.split(",")]

    if len(parts) != EXPECTED_VALUES:
        raise ValueError(f"Expected {EXPECTED_VALUES} values, got {len(parts)}")

    raw_values = [float(part) for part in parts]
    voltages = [adc_to_voltage(value) for value in raw_values]
    return raw_values, voltages


def create_csv_if_missing(csv_path: Path):
    if csv_path.exists():
        return

    header = ["timestamp", "label"]
    header += [f"raw_{pin}" for pin in PIN_NAMES]
    header += [f"voltage_{pin}" for pin in PIN_NAMES]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)


def append_sample(csv_path: Path, label: str, raw_values, voltages):
    row = [time.strftime("%Y-%m-%d %H:%M:%S"), label]
    row += [f"{x:.3f}" for x in raw_values]
    row += [f"{x:.6f}" for x in voltages]

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def normalize_label(user_input: str):
    user_input = user_input.strip()

    if len(user_input) != 1 or not user_input.isalpha():
        return None

    return user_input.upper()


class LatestFrame:
    def __init__(self):
        self.raw_values = None
        self.voltages = None
        self.lock = threading.Lock()


def receiver_loop(client_socket, latest_frame: LatestFrame):
    buffer = ""

    while True:
        data = client_socket.recv(1024)
        if not data:
            raise ConnectionError("Connection lost.")

        buffer += data.decode("utf-8")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()

            if not line:
                continue

            try:
                raw_values, voltages = parse_sensor_line(line)
                with latest_frame.lock:
                    latest_frame.raw_values = raw_values
                    latest_frame.voltages = voltages
            except ValueError:
                pass


def main():
    filename = input("CSV file name: ").strip() or "data"
    filename += ".csv"
    csv_path = OUTPUT_DIR / filename
    create_csv_if_missing(csv_path)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    print(f"\nData collector listening on {HOST}:{PORT}")
    print("Start python_server.py and ESP32 now.")
    print("Waiting for connection...")

    client_socket, client_address = server_socket.accept()
    print(f"Connected from {client_address}")

    latest_frame = LatestFrame()

    receiver_thread = threading.Thread(
        target=receiver_loop,
        args=(client_socket, latest_frame),
        daemon=True
    )
    receiver_thread.start()

    print("\nType any single letter A-Z and press Enter to save the latest sensor values.")
    print("Examples: a, b, d, w")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            user_input = input("Letter: ")
            label = normalize_label(user_input)

            if label is None:
                print("Please enter exactly one letter from A to Z.")
                continue

            with latest_frame.lock:
                raw_values = latest_frame.raw_values
                voltages = latest_frame.voltages

            if raw_values is None or voltages is None:
                print("No sensor data received yet.")
                continue

            append_sample(csv_path, label, raw_values, voltages)

            voltage_text = " ; ".join(f"{v:.2f}" for v in voltages) + " ;"
            print(f"Saved: {label} | {voltage_text}")

    except KeyboardInterrupt:
        print("\nStopping data collection.")

    finally:
        client_socket.close()
        server_socket.close()
        print(f"Data saved to: {csv_path}")


if __name__ == "__main__":
    main()