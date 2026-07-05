from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


def sanitize_value(value: object) -> object:
    """Replace NaN / Inf floats (from pandas) with None so they are JSON-safe."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def read_excel_records(file_path: str | Path) -> list[dict[str, object]]:
    dataframe = pd.read_excel(file_path)
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    return dataframe.to_dict(orient="records")


def clean_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    cleaned_records: list[dict[str, object]] = []
    seen_rows: set[tuple[tuple[str, object], ...]] = set()

    for record in records:
        cleaned_record: dict[str, object] = {}
        for key, value in record.items():
            # Sanitize NaN/Inf first so they don't break hashing or JSON
            safe_value = sanitize_value(value)
            if isinstance(safe_value, str):
                stripped = safe_value.strip()
                cleaned_record[key] = stripped if stripped else None
            else:
                cleaned_record[key] = safe_value

        # Use string representation for hashing to avoid unhashable types
        frozen_record = tuple(sorted((str(k), str(v)) for k, v in cleaned_record.items()))
        if frozen_record not in seen_rows:
            cleaned_records.append(cleaned_record)
            seen_rows.add(frozen_record)

    return cleaned_records


def build_dataframe(records: list[dict[str, object]]) -> pd.DataFrame:
    dataframe = pd.DataFrame(records)
    for column in dataframe.columns:
        if dataframe[column].dtype == "object":
            dataframe[column] = dataframe[column].apply(lambda value: value.strip() if isinstance(value, str) else value)
    return dataframe