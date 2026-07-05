from __future__ import annotations

from app.services.analytics.common import count_by_group, find_first_value, monthly_counts, ratio


def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    total_rows = len(rows)
    present_count = 0
    absent_count = 0

    for row in rows:
        status = str(find_first_value(row, ["attendance", "status", "presence", "present_absent"]) or "").strip().lower()
        if status in {"present", "p", "yes", "1", "available"}:
            present_count += 1
        elif status in {"absent", "a", "no", "0", "leave"}:
            absent_count += 1

    attendance_percentage = ratio(present_count, total_rows)
    absent_percentage = ratio(absent_count, total_rows)

    return {
        "domain": "Student Attendance",
        "kpis": {
            "attendance_percentage": attendance_percentage,
            "absent_percentage": absent_percentage,
            "monthly_attendance": monthly_counts(rows, ["attendance_date", "date", "day"]),
            "class_wise_attendance": count_by_group(rows, ["class", "section", "batch", "grade"]),
            "subject_wise_attendance": count_by_group(rows, ["subject", "course", "paper"]),
        },
        "charts": {
            "primary": monthly_counts(rows, ["attendance_date", "date", "day"]),
            "secondary": count_by_group(rows, ["class", "section", "batch", "grade"]),
        },
        "insights": [f"Attendance is {attendance_percentage}%.", f"Absence rate is {absent_percentage}%."] ,
    }