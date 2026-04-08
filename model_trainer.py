import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PIN_NAMES = ["D0", "D1", "D2", "D3", "D4", "D5", "D8", "D9", "D10"]
DEFAULT_CLASSES = ["A", "B", "D", "F", "H", "I", "O", "W", "unknown"]

DATASET_DIR = Path("./dataset")
MODEL_DIR = Path("./models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "asl_letter_model.joblib"
METADATA_PATH = MODEL_DIR / "asl_letter_model_metadata.json"

RANDOM_STATE = 42
TEST_SIZE = 0.2



def load_dataset(csv_path: Path):
    df = pd.read_csv(csv_path)

    required_columns = ["label"] + [f"voltage_{pin}" for pin in PIN_NAMES]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"CSV-tiedostosta puuttuvat sarakkeet: {missing}")

    df = df.dropna(subset=["label"])
    return df



def build_features(df: pd.DataFrame):
    feature_columns = [f"voltage_{pin}" for pin in PIN_NAMES]
    X = df[feature_columns].copy()
    y = df["label"].astype(str).copy()
    return X, y, feature_columns



def train_model(X_train, y_train):
    # StandardScaler ei ole RandomForestille välttämätön, mutta jätetään pipelineen,
    # jotta voitte helposti vaihtaa mallia myöhemmin.
    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=None,
                    min_samples_split=2,
                    min_samples_leaf=1,
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    return model



def print_results(model, X_test, y_test, classes):
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("\n=== TULOKSET ===")
    print(f"Test accuracy: {accuracy:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, labels=classes, zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=classes)
    cm_df = pd.DataFrame(cm, index=classes, columns=classes)
    print("Confusion matrix:")
    print(cm_df.to_string())



def save_outputs(model, classes, feature_columns):
    joblib.dump(model, MODEL_PATH)

    metadata = {
        "classes": classes,
        "feature_columns": feature_columns,
        "pin_names": PIN_NAMES,
        "model_type": "RandomForestClassifier",
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\nMalli tallennettu: {MODEL_PATH}")
    print(f"Metadata tallennettu: {METADATA_PATH}")



def main():
    default_csv = DATASET_DIR / "asl_dataset.csv"
    csv_input = input(f"Anna datasetin polku [{default_csv}]: ").strip()
    csv_path = Path(csv_input) if csv_input else default_csv

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset tiedostoa ei löydy: {csv_path}")

    df = load_dataset(csv_path)
    print(f"Luettiin {len(df)} riviä tiedostosta {csv_path}")

    label_counts = df["label"].value_counts().sort_index()
    print("\nLuokkajakauma:")
    print(label_counts.to_string())

    X, y, feature_columns = build_features(df)

    classes = sorted(set(DEFAULT_CLASSES) | set(y.unique()))

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(f"\nTrain-koko: {len(X_train)}")
    print(f"Test-koko:  {len(X_test)}")

    model = train_model(X_train, y_train)
    print_results(model, X_test, y_test, classes)
    save_outputs(model, classes, feature_columns)

    print("\nValmis. Tätä mallia alphabet_calculator.py voi käyttää reaaliaikaisessa luokittelussa.")


if __name__ == "__main__":
    main()
