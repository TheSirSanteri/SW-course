from pathlib import Path
from collections import Counter

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

PIN_NAMES = ["A0", "A1", "A2", "A3", "A4", "D7", "D8", "D9", "D10"]
FEATURE_COLUMNS = [f"voltage_{pin}" for pin in PIN_NAMES]

# Target letters for classification
TARGET_LETTERS = ["A", "B", "D", "F", "H", "I", "O", "W"]
UNKNOWN_LABEL = "unknown"



ALL_CLASSES = TARGET_LETTERS + [UNKNOWN_LABEL]

DATASET_DIR = Path("./datasets")
MODEL_DIR = Path("./models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODEL_DIR / "asl_letter_model.joblib"

TEST_SIZE = 0.20
RANDOM_STATE = 42


def find_dataset_files(dataset_dir: Path):
    csv_files = sorted(dataset_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {dataset_dir.resolve()}")
    return csv_files


def load_all_datasets(dataset_dir: Path):
    csv_files = find_dataset_files(dataset_dir)
    dataframes = []

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        df["source_file"] = csv_file.name
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df, csv_files


def validate_columns(df: pd.DataFrame):
    required_columns = ["label"] + FEATURE_COLUMNS
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")


def normalize_label(label):
    label = str(label).strip().upper()
    if label in TARGET_LETTERS:
        return label
    return UNKNOWN_LABEL

# Helper function to print class distribution in a readable format
def prepare_dataset(df: pd.DataFrame):
    validate_columns(df)

    df = df.dropna(subset=["label"]).copy()
    df["label"] = df["label"].apply(normalize_label)

    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=FEATURE_COLUMNS, how="all").copy()
    X = df[FEATURE_COLUMNS].copy()
    y = df["label"].copy()
    return df, X, y


def build_model():
    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )
    return model

def attach_model_info(model):
    model.target_letters_ = TARGET_LETTERS.copy()
    model.unknown_label_ = UNKNOWN_LABEL
    model.all_classes_ = ALL_CLASSES.copy()
    model.feature_columns_ = FEATURE_COLUMNS.copy()
    return model

def print_label_counts(title: str, labels):
    counts = Counter(labels)
    print(f"\n{title}")
    for class_name in ALL_CLASSES:
        print(f"  {class_name}: {counts.get(class_name, 0)}")


def main():
    print(f"Reading CSV files from: {DATASET_DIR.resolve()}")
    df, csv_files = load_all_datasets(DATASET_DIR)

    print("\nFiles used:")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")

    print(f"\nTotal raw rows: {len(df)}")

    df, X, y = prepare_dataset(df)
    print(f"Rows after cleaning: {len(df)}")

    print_label_counts("Class distribution after mapping", y)

    if len(df) < 10:
        raise ValueError("Not enough data for training. Collect more samples first.")

    if y.nunique() < 2:
        raise ValueError("Training requires at least two classes in the dataset.")

    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(f"\nTraining set:   {len(X_train)} rows (80%)")
    print(f"Validation set: {len(X_val)} rows (20%)")

    print_label_counts("Training distribution", y_train)
    print_label_counts("Validation distribution", y_val)

    model = build_model()
    model.fit(X_train, y_train)
    model = attach_model_info(model)

    y_pred = model.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)

    print("\n=== VALIDATION RESULTS ===")
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification report:")
    print(classification_report(y_val, y_pred, labels=ALL_CLASSES, zero_division=0))

    cm = confusion_matrix(y_val, y_pred, labels=ALL_CLASSES)
    cm_df = pd.DataFrame(cm, index=ALL_CLASSES, columns=ALL_CLASSES)
    print("Confusion matrix:")
    print(cm_df.to_string())

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to: {MODEL_PATH.resolve()}")
    print("This file can be used directly by alphabet_calculator.py")


if __name__ == "__main__":
    main()
