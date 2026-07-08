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
    """Bar chart showing non-null fill rate per column."""
    total = len(rows) or 1
    col_fill = {
        col: sum(1 for r in rows if r.get(col) not in (None, ""))
        for col in columns[:15]
    }
    ordered = sorted(col_fill.items(), key=lambda x: x[1], reverse=True)
    return {
        "labels": [k for k, _ in ordered],
        "values": [round(v / total * 100, 1) for _, v in ordered],
        "label": "Column Fill Rate (%)",
        "chart_type": "bar",
    }


def _numeric_by_category(
    rows: list[dict[str, object]], cat_col: str, num_col: str, limit: int = 12
) -> dict[str, object]:
    """Sum a numeric column grouped by a categorical column."""
    from collections import defaultdict
    buckets: dict[str, float] = defaultdict(float)
    for row in rows:
        cat = str(row.get(cat_col, "")).strip()
        val = parse_float(row.get(num_col))
        if cat and cat.lower() not in ("nan", "none", "") and val is not None:
            buckets[cat] += val
    if not buckets:
        return {"labels": [], "values": [], "label": f"{num_col} by {cat_col}", "chart_type": "bar"}
    ordered = sorted(buckets.items(), key=lambda x: x[1], reverse=True)[:limit]
    return {
        "labels": [k for k, _ in ordered],
        "values": [round(v, 2) for _, v in ordered],
        "label": f"{num_col} by {cat_col}",
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

    # Detect categorical columns (2–50 unique values)
    categorical_cols: list[str] = []
    for col in columns:
        unique_vals = {str(r.get(col, "")) for r in rows if r.get(col) not in (None, "")}
        if 2 <= len(unique_vals) <= 50:
            categorical_cols.append(col)

    # Detect numeric columns by actual values (not just name hints)
    numeric_cols: list[str] = []
    for col in columns:
        if col in categorical_cols:
            continue
        values = [parse_float(r.get(col)) for r in rows if r.get(col) not in (None, "")]
        numeric_values = [v for v in values if v is not None]
        if len(numeric_values) >= max(5, len(rows) * 0.3):
            numeric_cols.append(col)

    # Date columns
    date_cols = [c for c in columns if _is_date_col(c)]

    kpis = {
        "row_count": len(rows),
        "column_count": len(columns),
        "duplicate_rows": dupes,
        "missing_values": missing,
    }

    # ── Build 4 distinct charts, each from a DIFFERENT column ─────────────
    charts: dict[str, object] = {}
    chart_slots = ["primary", "secondary", "tertiary", "quaternary"]
    slot_idx = 0
    used_cols: set[str] = set()

    def add_chart(chart: dict[str, object], col: str) -> None:
        nonlocal slot_idx
        if slot_idx >= len(chart_slots):
            return
        if not chart.get("labels"):
            return
        charts[chart_slots[slot_idx]] = chart
        used_cols.add(col)
        slot_idx += 1

    # 1. Date trend line (if date col exists)
    if date_cols:
        c = _date_trend(rows, date_cols[0])
        if c.get("labels"):
            add_chart(c, date_cols[0])

    # 2. Categorical bar charts — one per unique categorical column
    for cat_col in categorical_cols:
        if slot_idx >= len(chart_slots):
            break
        if cat_col in used_cols:
            continue
        # If there's a numeric col, do "sum of numeric by category" (more insightful)
        paired_num = next((n for n in numeric_cols if n not in used_cols), None)
        if paired_num:
            c = _numeric_by_category(rows, cat_col, paired_num, limit=12)
            if c.get("labels"):
                add_chart(c, cat_col)
                used_cols.add(paired_num)
                continue
        c = _categorical_chart(rows, cat_col, limit=12)
        add_chart(c, cat_col)

    # 3. Numeric distribution for any remaining numeric cols
    for num_col in numeric_cols:
        if slot_idx >= len(chart_slots):
            break
        if num_col in used_cols:
            continue
        c = _numeric_distribution(rows, num_col)
        add_chart(c, num_col)

    # 4. Completeness chart as last resort if slots still empty
    if slot_idx < len(chart_slots):
        c = _completeness_chart(rows, columns)
        if c.get("labels"):
            charts[chart_slots[slot_idx]] = c
            slot_idx += 1

    # ── Insights ──────────────────────────────────────────────────────────
    insights: list[str] = []
    if num_summary.get("count", 0):
        insights.append(
            f"Dataset has {num_summary['count']} numeric values "
            f"(avg {num_summary['average']:,}, range {num_summary['minimum']:,}–{num_summary['maximum']:,})."
        )
    missing_total = missing.get("total", 0)
    if missing_total:
        total_cells = len(rows) * len(columns) or 1
        pct = round(missing_total / total_cells * 100, 1)
        insights.append(f"{missing_total} missing values detected ({pct}% of cells).")
    if dupes:
        insights.append(f"{dupes} duplicate rows found — deduplication recommended.")
    if date_cols:
        insights.append(f"Time series detected on '{date_cols[0]}' — trend chart included.")
    if categorical_cols:
        insights.append(
            f"{len(categorical_cols)} categorical column(s): "
            + ", ".join(f"'{c}'" for c in categorical_cols[:5])
            + ("…" if len(categorical_cols) > 5 else "") + "."
        )
    if not insights:
        insights.append("Dataset processed. Upload domain-specific files for richer analytics.")

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