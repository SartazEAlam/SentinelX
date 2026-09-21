"""Train and evaluate the baseline ML classifier for Phase 3."""

import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

# Define synthetic data for baseline
DATA = [
    # CREDENTIALS
    {"text": "DB_PASSWORD=super_secret_123", "label": "CREDENTIALS"},
    {"text": "aws_secret_access_key=AKIAIOSFODNN7EXAMPLE", "label": "CREDENTIALS"},
    {"text": "Here is the login: admin / password1234", "label": "CREDENTIALS"},
    # PAYMENT_CARD_DATA
    {"text": "My visa is 4111222233334444 and expires 12/25.", "label": "PAYMENT_CARD_DATA"},
    {"text": "Process this transaction for 5105105105105100", "label": "PAYMENT_CARD_DATA"},
    # HEALTH_DATA
    {"text": "Patient has a history of hypertension and diabetes.", "label": "HEALTH_DATA"},
    {"text": "Diagnosis: Acute myocardial infarction. Treat with aspirin.", "label": "HEALTH_DATA"},
    # PUBLIC
    {"text": "The company was founded in 2005 and provides DLP solutions.", "label": "PUBLIC"},
    {"text": "Press release: We are launching a new product line next week.", "label": "PUBLIC"},
    # INTERNAL_DOCUMENT
    {"text": "Please review the attached Q3 all-hands meeting minutes.", "label": "INTERNAL_DOCUMENT"},
    {"text": "The new PTO policy is effective starting January 1st.", "label": "INTERNAL_DOCUMENT"},
] * 10  # Multiply to have enough samples for train_test_split

def train_and_evaluate(model_dir: Path, report_path: Path):
    """Train the TF-IDF and Random Forest model, and evaluate it."""
    print(f"Training Baseline ML Model with {len(DATA)} samples...")
    
    df = pd.DataFrame(DATA)
    X = df["text"]
    y = df["label"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    vectorizer = TfidfVectorizer(max_features=1000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_vec, y_train)
    
    y_pred = model.predict(X_test_vec)
    report = classification_report(y_test, y_pred, zero_division=0)
    
    print("\n--- Evaluation Report ---")
    print(report)
    
    # Save artifacts
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, model_dir / "vectorizer.joblib")
    joblib.dump(model, model_dir / "model.joblib")
    joblib.dump(
        {"model_name": "RandomForest_Baseline", "model_version": "1.0.0"}, 
        model_dir / "metadata.joblib"
    )
    print(f"Models saved to {model_dir}")
    
    # Save markdown report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("# ML Baseline Evaluation Report\n\n")
        f.write("```text\n")
        f.write(report)
        f.write("\n```\n")
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    base_dir = Path(os.path.dirname(__file__)).parent
    model_dir = base_dir / "models"
    report_path = base_dir / "reports" / "classification_evaluation.md"
    
    train_and_evaluate(model_dir, report_path)
