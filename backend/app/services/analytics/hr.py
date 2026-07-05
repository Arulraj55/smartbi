from __future__ import annotations

from collections import Counter

from app.services.analytics.common import count_by_group, find_first_value, parse_float, ratio


def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    total_employees = len(rows)
    department_column = count_by_group(rows, ["department", "dept", "team"]).get("label")
    departments = {str(row.get(department_column)) for row in rows if department_column and row.get(department_column) not in (None, "")}
    gender_distribution = count_by_group(rows, ["gender", "sex"])

    salary_values = [parse_float(find_first_value(row, ["salary", "ctc", "annual_salary", "compensation"])) for row in rows]
    salary_values = [value for value in salary_values if value is not None]

    attendance_hits = 0
    attrition_count = 0
    experience_buckets = Counter()
    for row in rows:
        attendance_status = str(find_first_value(row, ["attendance_status", "status", "attendance"]) or "").strip().lower()
        if attendance_status in {"present", "active", "1", "yes"}:
            attendance_hits += 1
        attrition_status = str(find_first_value(row, ["attrition", "resigned", "left", "exit_status", "employment_status"]) or "").strip().lower()
        if attrition_status in {"yes", "true", "left", "resigned", "terminated"}:
            attrition_count += 1

        experience_value = parse_float(find_first_value(row, ["experience", "years_experience", "exp", "service_years"]))
        if experience_value is None:
            continue
        if experience_value <= 2:
            experience_buckets["0-2 years"] += 1
        elif experience_value <= 5:
            experience_buckets["3-5 years"] += 1
        elif experience_value <= 10:
            experience_buckets["6-10 years"] += 1
        else:
            experience_buckets["10+ years"] += 1

    department_performance = count_by_group(rows, ["department", "dept", "team"])

    return {
        "domain": "HR Management",
        "kpis": {
            "total_employees": total_employees,
            "department_count": len(departments),
            "gender_distribution": gender_distribution,
            "attendance_percentage": ratio(attendance_hits, total_employees),
            "average_salary": round(sum(salary_values) / len(salary_values), 2) if salary_values else 0.0,
            "experience_distribution": {"labels": list(experience_buckets.keys()), "values": list(experience_buckets.values())},
            "attrition_count": attrition_count,
            "department_performance": department_performance,
        },
        "charts": {
            "primary": department_performance,
            "secondary": gender_distribution,
        },
        "insights": [f"Attendance rate is {ratio(attendance_hits, total_employees)}%.", f"Attrition count is {attrition_count}."],
    }