import json
from typing import Dict, List, Tuple
import pandas as pd
from pathlib import Path


class ValidationError(Exception):
    """Raised when data validation fails critically."""
    pass


def validate_schema(
    df: pd.DataFrame,
    required_columns: List[str]
) -> None:
    """
    Ensure dataframe contains required columns.
    Fail hard if schema mismatch.
    """
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValidationError(
            f"Missing required columns: {missing}"
        )


def validate_nulls(
    df: pd.DataFrame,
    columns: List[str]
) -> Dict[str, int]:
    """
    Check null values in critical columns.
    """
    null_report = {}
    for col in columns:
        null_count = df[col].isnull().sum()
        null_report[col] = int(null_count)
        if null_count > 0:
            raise ValidationError(
                f"Column '{col}' contains {null_count} null values"
            )
    return null_report


def validate_text_length(
    df: pd.DataFrame,
    min_len: int,
    max_len: int,
    text_col: str = "text"
) -> Dict[str, int]:
    """
    Ensure all texts comply with length constraints.
    """
    lengths = df[text_col].str.len()
    too_short = int((lengths < min_len).sum())
    too_long = int((lengths > max_len).sum())

    if too_short > 0 or too_long > 0:
        raise ValidationError(
            f"Text length violation: "
            f"{too_short} too short, {too_long} too long"
        )

    return {
        "too_short": too_short,
        "too_long": too_long
    }


def validate_language(
    df: pd.DataFrame,
    target_lang: str,
    lang_col: str = "detected_lang"
) -> Dict[str, int]:
    """
    Validate language distribution.
    """
    invalid_lang = df[df[lang_col] != target_lang]
    count = len(invalid_lang)

    if count > 0:
        raise ValidationError(
            f"{count} rows not in target language '{target_lang}'"
        )

    return {
        "invalid_language_count": count
    }


def run_validation(
    df: pd.DataFrame,
    config: Dict,
    output_path: Path
) -> Dict:
    """
    Run full validation suite.
    """
    report = {
        "row_count": len(df),
        "checks": {},
        "status": "PASS"
    }

    try:
        validate_schema(df, ["id", "text"])
        report["checks"]["schema"] = "ok"

        report["checks"]["nulls"] = validate_nulls(df, ["id", "text"])

        report["checks"]["length"] = validate_text_length(
            df,
            config["cleaning"]["min_length"],
            config["cleaning"]["max_length"]
        )

        if config["cleaning"]["target_language"]:
            report["checks"]["language"] = validate_language(
                df,
                config["cleaning"]["target_language"]
            )

    except ValidationError as e:
        report["status"] = "FAIL"
        report["error"] = str(e)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if report["status"] == "FAIL":
        raise ValidationError(report["error"])

    return report
