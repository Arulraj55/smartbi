from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any

from app.services.database_service import DatabaseService
from app.services.openrouter_service import _call_openrouter


def _build_column_stats(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
    """Build per-column statistics so the AI can answer questions about the full dataset."""
    stats: dict[str, Any] = {}
    for col in columns:
        values = [r.get(col) for r in rows if r.get(col) not in (None, "")]
        total = len(values)
        if total == 0:
            stats[col] = {"type": "empty", "count": 0}
            continue

        # Try numeric
        numeric_vals = []
        for v in values:
            try:
                f = float(str(v).replace(",", ""))
                numeric_vals.append(f)
            except (ValueError, TypeError):
                pass

        numeric_ratio = len(numeric_vals) / total
        if numeric_ratio >= 0.8:
            s = sorted(numeric_vals)
            n = len(s)
            stats[col] = {
                "type": "numeric",
                "count": n,
                "sum": round(sum(s), 2),
                "mean": round(sum(s) / n, 2),
                "min": round(s[0], 2),
                "max": round(s[-1], 2),
                "median": round(s[n // 2], 2),
            }
        else:
            # Categorical — full frequency count
            counter = Counter(str(v).strip() for v in values)
            top = counter.most_common(20)
            stats[col] = {
                "type": "categorical",
                "count": total,
                "unique": len(counter),
                "top_values": {k: v for k, v in top},
            }
    return stats


def _build_grouped_aggregations(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
    """
    For each categorical column, compute sum/mean of every numeric column grouped by that category.
    This lets the AI answer 'top N by X' questions accurately.
    """
    # Identify numeric and categorical columns
    numeric_cols: list[str] = []
    categorical_cols: list[str] = []
    for col in columns:
        values = [r.get(col) for r in rows if r.get(col) not in (None, "")]
        if not values:
            continue
        numeric_vals = []
        for v in values:
            try:
                numeric_vals.append(float(str(v).replace(",", "")))
            except (ValueError, TypeError):
                pass
        if len(numeric_vals) / len(values) >= 0.8:
            numeric_cols.append(col)
        else:
            unique = len({str(v).strip() for v in values})
            if 2 <= unique <= 100:
                categorical_cols.append(col)

    aggregations: dict[str, Any] = {}
    for cat_col in categorical_cols[:4]:  # limit to 4 cat cols to keep prompt size small
        group_sums: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        group_counts: dict[str, int] = defaultdict(int)
        for row in rows:
            cat_val = str(row.get(cat_col, "")).strip()
            if not cat_val or cat_val.lower() in ("nan", "none", ""):
                continue
            group_counts[cat_val] += 1
            for num_col in numeric_cols[:6]:  # limit to 6 numeric cols
                v = row.get(num_col)
                try:
                    group_sums[cat_val][num_col] += float(str(v).replace(",", ""))
                except (ValueError, TypeError, AttributeError):
                    pass

        if not group_sums:
            continue

        # Sort by first numeric col descending, take top 20
        first_num = numeric_cols[0] if numeric_cols else None
        sorted_groups = sorted(
            group_sums.items(),
            key=lambda x: x[1].get(first_num, 0) if first_num else 0,
            reverse=True
        )[:20]

        aggregations[cat_col] = {
            "grouped_by": cat_col,
            "numeric_columns": numeric_cols[:6],
            "top_20_groups": [
                {
                    "value": group,
                    "count": group_counts[group],
                    **{num_col: round(sums[num_col], 2) for num_col in numeric_cols[:6]},
                }
                for group, sums in sorted_groups
            ],
        }

    return aggregations


def chat_with_dataset(upload_id: int, user_message: str, database_service: DatabaseService) -> str:
    upload = database_service.fetch_upload_by_id(upload_id)
    if upload is None:
        raise ValueError("Dataset upload not found.")

    rows = database_service.fetch_upload_rows(upload_id)
    if not rows:
        return "No data found in this upload."

    column_names = list(rows[0].keys())
    col_stats = _build_column_stats(rows, column_names)
    grouped = _build_grouped_aggregations(rows, column_names)

    domain_name = upload.get("domain_name", "Generic")
    total_rows = upload.get("row_count", len(rows))

    prompt = f"""You are SmartBI AI, a Business Intelligence assistant.
Answer the user's question using the FULL dataset statistics below.

Dataset: {upload.get("file_name")} | Domain: {domain_name} | Total Rows: {total_rows}
Columns: {column_names}

COLUMN STATISTICS (all {total_rows} rows):
{json.dumps(col_stats, indent=2)}

GROUPED AGGREGATIONS (pre-computed from all rows — use these for "top N by X" questions):
{json.dumps(grouped, indent=2)}

User Question: {user_message}

Instructions:
- Answer directly and precisely using the actual numbers from the stats above.
- The grouped aggregations show exact sums per category — use them for ranking/top-N questions.
- Write in plain text only. No markdown, no asterisks, no <br> tags, no HTML, no triple backticks.
- Use simple line breaks and spacing for readability. Numbered lists are fine.
- Never say "based on a sample" — you have full aggregated data for all {total_rows} rows.
- Be concise. Give the answer first, then brief explanation if needed.
"""
    try:
        return _call_openrouter(prompt)
    except Exception as exc:
        return f"Error analyzing data: {str(exc)}"
