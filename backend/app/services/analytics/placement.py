from __future__ import annotations

from app.services.analytics.common import count_by_group, find_first_value, monthly_counts, parse_float, ratio, sum_by_group


PLACEMENT_STATUS_WORDS = {"placed", "selected", "hired", "joined", "offer accepted", "converted"}


def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    total_students = len(rows)
    package_values = [
        parse_float(find_first_value(row, ["package", "ctc", "offer_ctc", "salary", "annual_salary"]))
        for row in rows
    ]
    package_values = [value for value in package_values if value is not None]

    placed_students = 0
    for row in rows:
        status_value = str(find_first_value(row, ["status", "placement_status", "offer_status", "result"]) or "").strip().lower()
        if status_value in PLACEMENT_STATUS_WORDS:
            placed_students += 1
        elif find_first_value(row, ["package", "ctc", "offer_ctc"]) is not None:
            placed_students += 1

    unplaced_students = max(total_students - placed_students, 0)

    kpis = {
        "total_students": total_students,
        "placed_students": placed_students,
        "unplaced_students": unplaced_students,
        "placement_percentage": ratio(placed_students, total_students),
        "average_package": round(sum(package_values) / len(package_values), 2) if package_values else 0.0,
        "highest_package": round(max(package_values), 2) if package_values else 0.0,
        "lowest_package": round(min(package_values), 2) if package_values else 0.0,
    }

    charts = {
        "company_wise_placements": count_by_group(rows, ["company", "company_name", "employer", "organization"]),
        "department_wise_placements": count_by_group(rows, ["department", "branch", "course", "specialization"]),
        "gender_wise_placements": count_by_group(rows, ["gender", "sex"]),
        "year_wise_placements": count_by_group(rows, ["year", "graduation_year", "passout_year", "academic_year"]),
    }

    insights = [
        f"Placement rate is {kpis['placement_percentage']}%.",
        f"Highest package recorded is {kpis['highest_package']}.",
    ]

    return {"domain": "Placement Management", "kpis": kpis, "charts": charts, "insights": insights}