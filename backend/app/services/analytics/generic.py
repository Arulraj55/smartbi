from __future__ import annotations

import math
import re
from collections import Counter

from app.services.analytics.common import (
    count_duplicate_rows,
    count_missing_values,
    extract_columns,
    numeric_summary,
    parse_float,
    top_frequencies,
)


# ── helpers ──────────────────────────────────────────────────────────────────

_DATE_HINTS = re.compile(
    r"date|time|day|month|year|created|updated|dob|joining|hire|drive|schedule",
    re.IGNORECASE,
)
_NUMERIC_HINTS = re.compile(
    r"amount|salary|ctc|score|marks|count|total|revenue|price|cost|qty|age|"
    r"quantity|percent|rate|value|package|fees|budget|stock|units",
    re.IGNORECASE,
)


def _is_date_col(col: str) -> bool:
    return bool(_DATE_HINTS.search(col))


def _is_numeric_col(col: str) -> bool:
    return bool(_NUMERIC_HINTS.search(col))


def _date_trend(rows: list[dict[str, object]], date_col: str) -> dict[str, object]:
    """Monthly count bucketing for any date-like column."""
    from app.services.analytics.common import parse_date
    counter: Counter[str] = Counter()
    for row in rows:
        parsed = parse_date(row.get(date_col))
        if parsed:
            counter[parsed.strftime("%Y-%m")] += 1
    ordered = sorted(counter.items())
    return {
        "labels": [k for k, _ in ordered],
        "values": [v for _, v in ordered],
        "label": date_col,
        "chart_type": "line",
    }


def _categorical_chart(
    rows: list[dict[str, object]], col: str, limit: int = 10
) -> dict[str, object]:
    counter = Counter(
        str(row.get(col, "")).strip()
        for row in rows
        if row.get(col) not in (None, "")
    )
    common = counter.most_common(limit)
    return {
        "labels": [label for label, _ in common],
        "values": [cnt for _, cnt in common],
        "label": col,
        "chart_type": "bar",
    }


def _numeric_distribution(
    rows: list[dict[str, object]], col: str
) -> dict[str, object]:
    """Bucket numeric values into 8 equal-width bins."""
    values = []
    for row in rows:
        v = parse_float(row.get(col))
        if v is not None and not (math.isnan(v) or math.isinf(v)):
            values.append(v)
    if len(values) < 5:
        return {"labels": [], "values": [], "label": col, "chart_type": "bar"}
    lo, hi = min(values), max(values)
    if lo == hi:
        return {
            "labels": [str(lo)],
            "values": [len(values)],
            "label": col,
            "chart_type": "bar",
        }
    bins = 8
    width = (hi - lo) / bins
    buckets: list[int] = [0] * bins
    labels: list[str] = []
    for i in range(bins):
        start = lo + i * width
        end = start + width
        labels.append(f"{start:.1f}–{end:.1f}")
    for v in values:
        idx = min(int((v - lo) / width), bins - 1)
        buckets[idx] += 1
    return {"labels": labels, "values": buckets, "label": col, "chart_type": "bar"}


def _completeness_chart(
    rows: list[dict[str, object]], columns: list[str]
) -> dict[str, object]:
    """Bar chart showing how many non-null values each column has."""
    total = len(rows) or 1
    col_fill = {
        col: sum(1 for r in rows if r.get(col) not in (None, ""))
        for col in columns[:15]
    }
    ordered = sorted(col_fill.items(), key=lambda x: x[1], reverse=True)
    return {
        "labels": [k for k, _ in ordered],
        "values": [round(v / total * 100, 1) for _, v in ordered],
        "label": "Column Completeness (%)",
        "chart_type": "bar",
    }


# ── main analyzer ─────────────────────────────────────────────────────────────

def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return _empty_result()

    columns = extract_columns(rows)
    num_summary = numeric_summary(rows)
    missing = count_missing_values(rows)
    dupes = count_duplicate_rows(rows)

    # Build frequency tables for categorical columns (≤20 unique values)
    freq_tables: dict[str, object] = {}
    categorical_cols: list[str] = []
    for col in columns:
        unique_vals = {str(r.get(col, "")) for r in rows if r.get(col) not in (None, "")}
        if 2 <= len(unique_vals) <= 20:
            freq_tables[col] = top_frequencies(rows, [col])
            categorical_cols.append(col)

    # Auto-detect chart sources
    date_cols = [c for c in columns if _is_date_col(c)]
    numeric_cols = [c for c in columns if _is_numeric_col(c) and c not in categorical_cols]

    kpis = {
        "row_count": len(rows),
        "column_count": len(columns),
        "missing_values": missing,
        "duplicate_rows": dupes,
        "numeric_summary": num_summary,
        "frequency_tables": freq_tables,
        "date_distribution": (
            _date_trend(rows, date_cols[0]) if date_cols else {"labels": [], "values": [], "label": "Date"}
        ),
    }

    # ── Chart generation (up to 4 charts) ─────────────────────────────────
    charts: dict[str, object] = {}

    # Chart 1 — date trend (line chart)
    if date_cols:
        charts["primary"] = _date_trend(rows, date_cols[0])
    elif categorical_cols:
        charts["primary"] = _categorical_chart(rows, categorical_cols[0])
    else:
        charts["primary"] = _completeness_chart(rows, columns)

    # Chart 2 — first categorical column (bar chart)
    cat_used = 0
    if categorical_cols:
        charts["secondary"] = _categorical_chart(rows, categorical_cols[0])
        cat_used = 1
    elif numeric_cols:
        charts["secondary"] = _numeric_distribution(rows, numeric_cols[0])
    else:
        charts["secondary"] = _completeness_chart(rows, columns)

    # Chart 3 — second categorical or first numeric distribution
    if len(categorical_cols) > cat_used:
        charts["tertiary"] = _categorical_chart(rows, categorical_cols[cat_used])
    elif numeric_cols:
        charts["tertiary"] = _numeric_distribution(rows, numeric_cols[0])
    else:
        charts["tertiary"] = _completeness_chart(rows, columns)

    # Chart 4 — column completeness overview
    charts["quaternary"] = _completeness_chart(rows, columns)

    # ── Insights ──────────────────────────────────────────────────────────
    insights: list[str] = []
    if num_summary.get("count", 0):
        insights.append(
            f"Found {num_summary['count']} numeric values across all columns "
            f"(avg {num_summary['average']}, min {num_summary['minimum']}, max {num_summary['maximum']})."
        )
    total = len(rows) or 1
    missing_total = missing.get("total", 0)
    if missing_total:
        pct = round(missing_total / (total * len(columns)) * 100, 1)
        insights.append(f"{missing_total} missing values found ({pct}% of all cells).")
    if dupes:
        insights.append(f"{dupes} duplicate rows detected — consider deduplication.")
    if date_cols:
        insights.append(f"Date column detected: '{date_cols[0]}'. Trend chart generated.")
    if categorical_cols:
        insights.append(
            f"{len(categorical_cols)} categorical column(s) identified: "
            + ", ".join(f"'{c}'" for c in categorical_cols[:4])
            + ("…" if len(categorical_cols) > 4 else "")
            + "."
        )
    if not insights:
        insights.append("Dataset processed successfully. Upload domain-specific files for richer analytics.")

    return {
        "domain": "Generic",
        "kpis": kpis,
        "charts": charts,
        "insights": insights,
    }


def _empty_result() -> dict[str, object]:
    empty_chart: dict[str, object] = {"labels": [], "values": [], "label": "No Data", "chart_type": "bar"}
    return {
        "domain": "Generic",
        "kpis": {"row_count": 0, "column_count": 0},
        "charts": {"primary": empty_chart, "secondary": empty_chart},
        "insights": ["No data rows found in the uploaded file."],
    }


def build_frequency_tables(rows: list[dict[str, object]], columns: list[str]) -> dict[str, object]:
    tables: dict[str, object] = {}
    for column in columns:
        unique_values = {str(row.get(column, "")) for row in rows if row.get(column) not in (None, "")}
        if not unique_values or len(unique_values) > 20:
            continue
        tables[column] = top_frequencies(rows, [column])
    return tables


def first_frequency_chart(frequency_tables: dict[str, object]) -> dict[str, object]:
    for column_name, chart in frequency_tables.items():
        if isinstance(chart, dict) and chart.get("labels"):
            return {"labels": chart["labels"], "values": chart["values"], "label": column_name, "chart_type": "bar"}
    return {"labels": [], "values": [], "label": "Frequency", "chart_type": "bar"}