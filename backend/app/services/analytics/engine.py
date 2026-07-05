from __future__ import annotations

from app.services.analytics.dispatcher import build_analytics_payload


def analyze_dataset(rows: list[dict[str, object]]) -> dict[str, object]:
    row_list = list(rows)
    payload = build_analytics_payload(row_list)
    return {
        "domain": payload["domain"],
        "row_count": len(row_list),
        "column_count": len(row_list[0].keys()) if row_list else 0,
        "kpis": payload.get("kpis", {}),
        "charts": payload.get("charts", {}),
        "insights": payload.get("insights", []),
        "raw": payload.get("analytics", {}),
    }