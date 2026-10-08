"""Dataset loader and splitter for Phase 9 evaluation."""

import json
from pathlib import Path
from typing import Any
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42
TEST_SIZE = 0.30

def load_dataset() -> list[dict[str, Any]]:
    """Loads the generated synthetic dataset."""
    dataset_path = Path(__file__).resolve().parent.parent / "dataset" / "synthetic_data.json"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Synthetic dataset not found at {dataset_path}. Run generator.py first.")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_train_test_split(test_size: float = TEST_SIZE, random_state: int = RANDOM_SEED):
    """Splits the synthetic dataset into stratified Train and Test sets.
    
    Returns:
        (train_samples, test_samples)
    """
    samples = load_dataset()
    labels = [1 if s["is_sensitive"] else 0 for s in samples]

    train_samples, test_samples = train_test_split(
        samples,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    return train_samples, test_samples

if __name__ == "__main__":
    train_s, test_s = get_train_test_split()
    train_pos = sum(1 for s in train_s if s["is_sensitive"])
    test_pos = sum(1 for s in test_s if s["is_sensitive"])
    print(f"Train samples: {len(train_s)} (Sensitive: {train_pos}, Benign: {len(train_s) - train_pos})")
    print(f"Test samples : {len(test_s)} (Sensitive: {test_pos}, Benign: {len(test_s) - test_pos})")
