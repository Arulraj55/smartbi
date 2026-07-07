from __future__ import annotations

import json
import math
import os
import urllib.request
import urllib.error
from collections import defaultdict
from typing import Any


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")

# Hard timeout for the OpenRouter HTTP call — keep well under gunicorn's 120s
# to leave time for DB inserts and other processing.
_OPENROUTER_TIMEOUT = 20


def _call_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in environment.")

    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 600,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://smartbi-backend.onrender.com",
            "X-Title": "SmartBI",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=_OPENROUTER_TIMEOUT) as response:
        result = json.loads(response.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"].strip()


def _safe_float(val: Any) -> float | None:
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _build_chart_data(
    rows: list[dict[str, Any]],
    label_col: str,
    value_col: str,
    agg: str = "sum",
    top_n: int = 15,
) -> dict[str, Any]:
    """Aggregate rows by label_col, compute value_col metric."""
    buckets: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        label = str(row.get(label_col, "")).strip()
        if not label or label.lower() in ("nan", "none", ""):
            continue
        val = _safe_float(row.get(value_col))
        if val is not None:
            buckets[label].append(val)

    if not buckets:
        return {"labels": [], "values": []}

    if agg == "sum":
        aggregated = {k: round(sum(v), 2) for k, v in buckets.items()}
    elif agg == "avg":
        aggregated = {k: round(sum(v) / len(v), 2) for k, v in buckets.items()}
    elif agg == "count":
        aggregated = {k: len(v) for k, v in buckets.items()}
    else:
        aggregated = {k: round(sum(v), 2) for k, v in buckets.items()}

    # Sort by value descending, take top N
    sorted_items = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)[:top_n]
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    return {"labels": labels, "values": values}


def detect_domain_ai(
    column_names: list[str],
    sample_rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Use OpenRouter AI to detect domain, decide visualizations,
    then compute actual chart data from the rows.
    """
    # Limit sample to 3 rows and truncate values to keep prompt small and fast
    sample_data = [{k: str(v)[:40] for k, v in row.items()} for row in sample_rows[:3]]

    prompt = (
        "You are a data analyst. Respond ONLY with valid JSON, no markdown.\n\n"
        f"Columns: {column_names}\n"
        f"Sample (3 rows): {json.dumps(sample_data)}\n\n"
        "Return ONLY this JSON:\n"
        '{"domain":"<IPL Cricket|Placement Management|HR Management|Retail Sales|Inventory|Student Attendance|Finance|Generic>",'
        '"confidence":<0-100>,'
        '"reason":"<one sentence>",'
        '"kpis":[{"label":"<name>","column":"<col>","agg":"sum|avg|count"}],'
        '"visualizations":[{"title":"<t>","type":"bar|line|pie|doughnut","label_col":"<col>","value_col":"<col>","agg":"sum|avg|count","description":"<one line>"}],'
        '"insights":["<insight1>","<insight2>","<insight3>"]}\n\n'
        "Rules: 4 kpis, exactly 4 visualizations using different value_col each, 3 insights."
    )

    try:
        raw = _call_openrouter(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        ai = json.loads(raw.strip())
        ai["ai_powered"] = True

        # Now compute actual chart data from rows
        rows = all_rows or sample_rows
        computed_charts = []

        for viz in ai.get("visualizations", []):
            label_col = viz.get("label_col", "")
            value_col = viz.get("value_col", "")
            agg = viz.get("agg", "sum")

            if not label_col or not value_col:
                continue

            chart_data = _build_chart_data(rows, label_col, value_col, agg)

            if not chart_data["labels"]:
                continue

            computed_charts.append({
                "title": viz.get("title", value_col),
                "type": viz.get("type", "bar"),
                "description": viz.get("description", ""),
                "labels": chart_data["labels"],
                "values": chart_data["values"],
                "label_col": label_col,
                "value_col": value_col,
            })

        # Compute KPI values
        computed_kpis = {}
        for kpi in ai.get("kpis", []):
            col = kpi.get("column", "")
            agg = kpi.get("agg", "sum")
            label = kpi.get("label", col)
            if not col:
                continue
            vals = [_safe_float(r.get(col)) for r in rows if _safe_float(r.get(col)) is not None]
            if not vals:
                continue
            if agg == "sum":
                computed_kpis[label] = round(sum(vals), 2)
            elif agg == "avg":
                computed_kpis[label] = round(sum(vals) / len(vals), 2)
            elif agg == "count":
                computed_kpis[label] = len(vals)

        ai["computed_charts"] = computed_charts
        ai["computed_kpis"] = computed_kpis
        return ai

    except Exception as exc:
        return {
            "domain": "Generic",
            "confidence": 0,
            "reason": f"AI detection failed: {str(exc)}",
            "visualizations": [],
            "computed_charts": [],
            "computed_kpis": {},
            "kpis": [],
            "insights": [],
            "ai_powered": False,
            "error": str(exc),
        }
