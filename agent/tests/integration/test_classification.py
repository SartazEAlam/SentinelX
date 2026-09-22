"""Integration tests for the Classification Engine."""

import json
from pathlib import Path

import pytest
from sentinel_agent.classification import SensitivityLevel
from sentinel_agent.classification.engine import ClassificationEngine


@pytest.fixture
def engine(tmp_path: Path):
    """Provide a ClassificationEngine configured for testing."""
    config_path = tmp_path / "classification_rules.json"

    config = {
        "sensitivity_levels": {
            "UNKNOWN": 0, "PUBLIC": 10, "INTERNAL": 30, "CONFIDENTIAL": 60, "HIGHLY_CONFIDENTIAL": 90
        },
        "rules": {
            "extensions": {
                ".env": {"confidence": 0.8, "category": "AUTHENTICATION_SECRETS", "evidence": "env file"}
            },
            "filenames": [
                {"pattern": ".*salary.*", "confidence": 0.7, "category": "EMPLOYEE_DATA", "evidence": "salary file"}
            ],
            "keywords": [
                {"keyword": "confidential", "confidence": 0.4, "category": "CONFIDENTIAL_DOCUMENT", "evidence": "keyword"}
            ],
            "regex": [
                {
                    "name": "api_key",
                    "pattern": "AKIA[0-9A-Z]{16}",
                    "confidence": 0.9,
                    "category": "CREDENTIALS",
                    "evidence": "AWS Key"
                }
            ]
        }
    }

    with open(config_path, "w") as f:
        json.dump(config, f)

    return ClassificationEngine(config_path=config_path, ml_dir=None)


def test_classify_public_text(engine: ClassificationEngine, tmp_path: Path):
    file_path = tmp_path / "readme.txt"
    with open(file_path, "w") as f:
        f.write("This is a normal file without secrets.")

    result = engine.classify_file(file_path)
    assert result.sensitivity_level == SensitivityLevel.PUBLIC
    assert result.content_inspected is True


def test_classify_credential_regex(engine: ClassificationEngine, tmp_path: Path):
    file_path = tmp_path / "config.txt"
    with open(file_path, "w") as f:
        f.write("aws_access_key_id=AKIAIOSFODNN7EXAMPLE")

    result = engine.classify_file(file_path)
    assert result.sensitivity_level == SensitivityLevel.HIGHLY_CONFIDENTIAL
    assert "CREDENTIALS" in result.categories
    assert len(result.evidence) == 1
    assert result.evidence[0].source == "regex"
    assert result.evidence[0].redacted_value == "****************MPLE"


def test_classify_extension(engine: ClassificationEngine, tmp_path: Path):
    file_path = tmp_path / ".env"
    with open(file_path, "w") as f:
        f.write("FOO=bar")

    result = engine.classify_file(file_path)
    assert result.sensitivity_level == SensitivityLevel.CONFIDENTIAL
    assert "AUTHENTICATION_SECRETS" in result.categories


def test_classify_filename(engine: ClassificationEngine, tmp_path: Path):
    file_path = tmp_path / "2023_salary_report.csv"
    with open(file_path, "w") as f:
        f.write("id,amount\n1,100")

    result = engine.classify_file(file_path)
    assert result.sensitivity_level == SensitivityLevel.CONFIDENTIAL
    assert "EMPLOYEE_DATA" in result.categories
