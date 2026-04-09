import socket
import sys
from pathlib import Path
import pandas as pd

import numpy as np
import joblib

HOST = "127.0.0.1"
PORT = 6000


PIN_NAMES = ["A0", "A1", "A2", "A3", "A4", "D7", "D8", "D9", "D10"]
EXPECTED_VALUES = len(PIN_NAMES)
ADC_MAX = 4095.0
REFERENCE_VOLTAGE = 3.3

# Model path
MODEL_PATH = Path("./models/asl_letter_model.joblib")

# threshold for classifying a prediction as "unknown" if the confidence is too low
UNKNOWN_THRESHOLD = 0.60

FEATURE_COLUMNS = [f"voltage_{pin}" for pin in PIN_NAMES]

def adc_to_voltage(raw_value: float) -> float:
    return (raw_value / ADC_MAX) * REFERENCE_VOLTAGE


def parse_sensor_line(line: str):
    parts = [part.strip() for part in line.split(",")]

    if len(parts) != EXPECTED_VALUES:
        raise ValueError(f"Expected {EXPECTED_VALUES} values, got {len(parts)}")

    raw_values = [float(part) for part in parts]
    voltages = [adc_to_voltage(value) for value in raw_values]
    return raw_values, voltages


def build_feature_vector(raw_values, voltages):
    return pd.DataFrame([voltages], columns=FEATURE_COLUMNS)


def get_recognized_letters(model):
    if hasattr(model, "target_letters_"):
        return list(model.target_letters_)

    if hasattr(model, "classes_"):
        return [cls for cls in model.classes_ if str(cls).lower() != "unknown"]

    return []

def load_model():
    if not MODEL_PATH.exists():
        # Error handling
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}\n"
        )

    model = joblib.load(MODEL_PATH)
    return model

def predict_letter(model, raw_values, voltages):
    features = build_feature_vector(raw_values, voltages)

    # first try to use predict_proba if available for confidence estimation, otherwise fall back to predict
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)[0]
        best_index = int(np.argmax(probabilities))
        best_probability = float(probabilities[best_index])

        if hasattr(model, "classes_"):
            model_classes = list(model.classes_)
        else:
            raise ValueError("Model does not contain classes_.")
        
        predicted_label = str(model_classes[best_index])

        if best_probability < UNKNOWN_THRESHOLD:
            return "unknown", best_probability, dict(zip(model_classes, probabilities))

        return predicted_label, best_probability, dict(zip(model_classes, probabilities))

    # backup: if predict_proba is not available, just use predict without confidence estimation
    predicted_label = str(model.predict(features)[0])
    return predicted_label, None, None

def print_status_inline(voltages, predicted_label):
    voltage_text = " ; ".join(f"{v:.2f}" for v in voltages) + " ;"
    status = f"Voltages: {voltage_text} | Letter: {predicted_label}"

    sys.stdout.write("\r" + status.ljust(200))
    sys.stdout.flush()



def main():
    model = load_model()
    recognized_letters = get_recognized_letters(model)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    print(f"Realtime classifier listening on {HOST}:{PORT}")
    print(f"Recognized letters: {', '.join(recognized_letters)}")
    print("Waiting for data from local server...")

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
                    raw_values, voltages = parse_sensor_line(line)
                    predicted_label, _, _ = predict_letter(
                        model, raw_values, voltages
                    )
                    print_status_inline(voltages, predicted_label)

                except ValueError as e:
                    sys.stdout.write("\r" + f"Invalid data: {e}".ljust(200))
                    sys.stdout.flush()

                except Exception as e:
                    sys.stdout.write("\r" + f"Classification problem: {e}".ljust(200))
                    sys.stdout.flush()

    except KeyboardInterrupt:
        print("\nProcessor stopped.")

    finally:
        client_socket.close()
        server_socket.close()


if __name__ == "__main__":
    main()