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
    df = pd.DataFrame({
        "id": ["msg_001"],
        "text": ["transaksi gagal"]
    })
    validate_schema(df, ["id", "text"])

def test_validate_schema_fail_missing_column():
    df = pd.DataFrame({"text": ["transaksi gagal"]})
    with pytest.raises(ValidationError, match="Missing required columns"):
        validate_schema(df, ["id", "text"])

def test_validate_nulls_pass():
    df = pd.DataFrame({
        "id": ["msg_001", "msg_002"],
        "text": ["transaksi gagal", "top up gagal"]
    })
    result = validate_nulls(df, ["id", "text"])
    assert result["id"] == 0
    assert result["text"] == 0

def test_validate_nulls_fail():
    df = pd.DataFrame({
        "id": ["msg_001"],
        "text": [None]
    })
    with pytest.raises(ValidationError, match="contains .* null values"):
        validate_nulls(df, ["id", "text"])

def test_validate_text_length_pass():
    df = pd.DataFrame({
        "id": ["msg_001"],
        "text": ["transaksi gagal tapi duit udh kepotong"]
    })
    result = validate_text_length(df, min_len=20, max_len=300)
    assert result["too_short"] == 0
    assert result["too_long"] == 0

def test_validate_text_length_fail_too_short():
    df = pd.DataFrame({
        "id": ["msg_001"],
        "text": ["hi"]
    })
    with pytest.raises(ValidationError, match="Text length violation"):
        validate_text_length(df, min_len=20, max_len=300)

def test_validate_text_length_fail_too_long():
    df = pd.DataFrame({
        "id": ["msg_001"],
        "text": ["x" * 400]
    })
    with pytest.raises(ValidationError, match="Text length violation"):
        validate_text_length(df, min_len=20, max_len=300)