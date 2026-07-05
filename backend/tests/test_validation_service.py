from app.services.validation_service import validate_records


def test_validate_records_flags_duplicates_and_invalid_dates() -> None:
    records = [
        {"candidate_name": "Asha", "joining_date": "2026-01-01"},
        {"candidate_name": "Asha", "joining_date": "2026-01-01"},
        {"candidate_name": "Ben", "joining_date": "invalid-date"},
    ]

    result = validate_records(records, ["candidate_name", "joining_date"])

    assert result.is_valid is False
    assert any("Duplicate row" in warning for warning in result.warnings)
    assert any("Invalid date" in error for error in result.errors)