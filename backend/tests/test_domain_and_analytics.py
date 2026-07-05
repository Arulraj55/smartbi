from app.services.analytics.engine import analyze_dataset
from app.services.analytics_service import calculate_percentages, calculate_rankings, calculate_summary_metrics, calculate_trends
from app.services.domain_service import detect_domain


def test_detect_domain_identifies_placement_columns() -> None:
    domain_name, confidence = detect_domain(["Candidate Name", "Interview Date", "Offer CTC"])

    assert domain_name == "Placement Management"
    assert confidence > 0


def test_calculate_summary_metrics_counts_rows_and_domains() -> None:
    rows = [
        {"detected_domain": "Placement", "amount": 100},
        {"detected_domain": "Placement", "amount": 200},
        {"detected_domain": "HR", "amount": 300},
    ]

    summary = calculate_summary_metrics(rows)

    assert summary["total_rows"] == 3
    assert summary["average_numeric_value"] == 200.0
    assert summary["domain_breakdown"]["Placement"] == 2


def test_calculate_rankings_percentages_and_trends() -> None:
    rows = [
        {"name": "A", "score": 90, "category": "X", "date": "2026-01-01"},
        {"name": "B", "score": 80, "category": "X", "date": "2026-01-15"},
        {"name": "C", "score": 95, "category": "Y", "date": "2026-02-01"},
    ]

    rankings = calculate_rankings(rows, "score")
    percentages = calculate_percentages(rows, "category")
    trends = calculate_trends(rows, "date", "score")

    assert rankings[0]["name"] == "C"
    assert percentages["X"] == 66.67
    assert trends[0]["month"] == "2026-01"


def test_analyze_dataset_returns_generic_for_unknown_columns() -> None:
    result = analyze_dataset([
        {"notes": "alpha", "remarks": "beta"},
        {"notes": "alpha", "remarks": "gamma"},
    ])

    assert result["domain"]["name"] == "Generic"
    assert result["row_count"] == 2