from pathlib import Path

import pandas as pd

from app.services.processing_service import process_excel_file


def test_process_excel_file_detects_domain_and_builds_summary(tmp_path: Path) -> None:
    excel_path = tmp_path / "placement.xlsx"
    dataframe = pd.DataFrame(
        [
            {"Candidate Name": "Asha", "Interview Date": "2026-01-01", "Offer CTC": 12.5},
            {"Candidate Name": "Ben", "Interview Date": "2026-01-15", "Offer CTC": 14.0},
        ]
    )
    dataframe.to_excel(excel_path, index=False)

    result = process_excel_file(excel_path, "placement.xlsx", None)

    assert result.domain_name == "Placement Management"
    assert result.validation.is_valid is True
    assert result.row_count == 2
    assert result.summary["total_rows"] == 2
    assert result.summary["monthly_summary"]["2026-01"] == 2