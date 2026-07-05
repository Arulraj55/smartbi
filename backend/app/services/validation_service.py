from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_records(records: list[dict[str, object]], required_columns: list[str]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not records:
        return ValidationResult(False, ["No records found in workbook."], warnings)

    missing_columns = [column for column in required_columns if column not in records[0]]
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")

    seen_rows: set[tuple[tuple[str, object], ...]] = set()
    for index, record in enumerate(records, start=1):
        frozen_record = tuple(sorted(record.items()))
        if frozen_record in seen_rows:
            warnings.append(f"Duplicate row detected at record {index}.")
        seen_rows.add(frozen_record)

        for key, value in record.items():
            if isinstance(value, str) and not value.strip():
                warnings.append(f"Empty value found in column '{key}' at record {index}.")
            if key.lower().endswith("date") and isinstance(value, str):
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    errors.append(f"Invalid date in column '{key}' at record {index}: {value}")

            if key.lower().endswith(("amount", "salary", "qty", "quantity")) and value is not None:
                try:
                    float(value)
                except (TypeError, ValueError):
                    errors.append(f"Invalid numeric value in column '{key}' at record {index}: {value}")

    return ValidationResult(not errors, errors, warnings)