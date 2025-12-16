import pandas as pd
import pytest
from pathlib import Path

from scripts.validate import (
    validate_schema,
    validate_nulls,
    validate_text_length,
    ValidationError
)


def test_validate_schema_pass():
    df = pd.DataFrame({"id": ["1"], "text": ["halo"]})
    validate_schema(df, ["id", "text"])


def test_validate_schema_fail():
    df = pd.DataFrame({"text": ["halo"]})
    with pytest.raises(ValidationError):
        validate_schema(df, ["id", "text"])


def test_validate_nulls_fail():
    df = pd.DataFrame({"id": ["1"], "text": [None]})
    with pytest.raises(ValidationError):
        validate_nulls(df, ["id", "text"])


def test_validate_text_length_fail():
    df = pd.DataFrame({
        "id": ["1"],
        "text": ["hi"]
    })
    with pytest.raises(ValidationError):
        validate_text_length(df, min_len=5, max_len=100)
