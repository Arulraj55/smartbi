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


def chat_with_dataset(upload_id: int, user_message: str, database_service: DatabaseService) -> str:
    upload = database_service.fetch_upload_by_id(upload_id)
    if upload is None:
        raise ValueError("Dataset upload not found.")

    rows = database_service.fetch_upload_rows(upload_id)
    if not rows:
        return "No data found in this upload."

    column_names = list(rows[0].keys())
    col_stats = _build_column_stats(rows, column_names)

    domain_name = upload.get("domain_name", "Generic")
    total_rows = upload.get("row_count", len(rows))

    prompt = f"""You are SmartBI AI, a Business Intelligence assistant.
Answer the user's question using the FULL dataset statistics below.

### Dataset Info
- File: {upload.get("file_name")}
- Domain: {domain_name}
- Total Rows: {total_rows}
- Columns: {column_names}

### Full Column Statistics (computed from ALL {total_rows} rows)
{json.dumps(col_stats, indent=2)}

### User Question
{user_message}

### Instructions
- Use the column statistics above to answer accurately about the FULL dataset, not a sample.
- For categorical columns, "top_values" shows the exact count for each unique value across all rows.
- For numeric columns, use sum/mean/min/max/median as appropriate.
- Be direct and precise. Use the actual numbers from the stats.
- Format your answer clearly. Use tables or bullet points where helpful.
- Do not say "based on a sample" — you have full aggregated data for all {total_rows} rows.
"""
    try:
        return _call_openrouter(prompt)
    except Exception as exc:
        return f"Error analyzing data: {str(exc)}"
