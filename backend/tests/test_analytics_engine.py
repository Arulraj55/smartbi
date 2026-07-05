from app.services.analytics.engine import analyze_dataset


def test_placement_analytics_calculations_are_structured() -> None:
    rows = [
        {"Candidate Name": "Asha", "Company": "TechNova", "Department": "CSE", "Gender": "F", "Interview Date": "2026-01-01", "Offer CTC": 12.5, "Status": "Selected", "Year": 2026},
        {"Candidate Name": "Ben", "Company": "TechNova", "Department": "ECE", "Gender": "M", "Interview Date": "2026-01-15", "Offer CTC": 14.0, "Status": "Placed", "Year": 2026},
    ]

    result = analyze_dataset(rows)

    assert result["domain"]["name"] == "Placement Management"
    assert result["kpis"]["total_students"] == 2
    assert result["kpis"]["placed_students"] == 2
    assert result["kpis"]["placement_percentage"] == 100.0


def test_empty_dataset_returns_generic_zero_values() -> None:
    result = analyze_dataset([])

    assert result["domain"]["name"] == "Generic"
    assert result["row_count"] == 0
    assert result["kpis"]["row_count"] == 0