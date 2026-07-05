# SmartBI Backend

This folder contains the Flask API, validation, analytics, and persistence layers for SmartBI.

## Analytics API

The analytics engine now exposes authenticated GET endpoints under `/api/analytics`:

- `/api/analytics/summary`
- `/api/analytics/domain`
- `/api/analytics/kpis`
- `/api/analytics/charts`
- `/api/analytics/drilldown`
- `/api/analytics/compare`

Optional query string support:

- `upload_id` to target a specific uploaded workbook

These endpoints require an authenticated admin session and return JSON responses intended for Chart.js and Power BI consumption.

Each endpoint accepts an optional `upload_id` query string. When omitted, the latest upload is used.

## Drill-down API

`GET /api/analytics/drilldown` returns source rows behind a chart slice or KPI card.

Supported query strings:

- `field` or `dimension` with `value` or `label`, for example `field=company&value=TechNova`
- `metric` or `kpi`, for example `metric=low_stock`
- `limit` and `offset` for pagination
- `upload_id` to target a specific upload

The response includes `rows`, `columns`, `drilldown` metadata, and analytics recalculated for the matched rows.

## Historical Comparison API

`GET /api/analytics/compare` compares two uploaded datasets from the same detected domain.

Required query strings:

- `upload_a`: older or baseline upload ID
- `upload_b`: newer upload ID

Optional query strings:

- `chart=true` to include Chart.js-ready payloads
- `summary_only=true` to omit the raw per-upload analytics snapshot

Example:

```http
GET /api/analytics/compare?upload_a=1&upload_b=2&chart=true
```

Response shape:

```json
{
  "domain": "Retail Sales",
  "upload_a": {"id": 1, "file_name": "sales_old.xlsx"},
  "upload_b": {"id": 2, "file_name": "sales_new.xlsx"},
  "comparison": {
    "total_revenue": {
      "old": 120000,
      "new": 154000,
      "difference": 34000,
      "growth_percent": 28.33,
      "trend": "Increase"
    }
  },
  "charts": {
    "bar_chart": {"labels": [], "datasets": []},
    "line_chart": {"labels": [], "datasets": []},
    "comparison_chart": {"labels": [], "old_values": [], "new_values": []},
    "trend_chart": {"labels": [], "values": [], "label": "Growth %"}
  }
}
```

The API returns `400` for missing parameters, empty uploads, or domain mismatches, and `404` when either upload does not exist.

## Reports API

`GET /api/reports` returns report metadata and supported export formats.

`GET /api/reports/download` generates a report file.

Required query strings:

- `upload_id`: uploaded dataset ID
- `format`: one of `pdf`, `excel`, `csv`, or `json`

Optional query strings:

- `compare=true` to export a comparison report
- `upload_b`: second upload ID when `compare=true`
- Analytics filter parameters such as `start_date`, `end_date`, `department`, `company`, `category`, `region`, `gender`, `year`, or `search_keyword`

Examples:

```http
GET /api/reports/download?upload_id=1&format=pdf
GET /api/reports/download?upload_id=1&format=excel&department=CSE
GET /api/reports/download?upload_id=1&format=csv&compare=true&upload_b=2
```

Report exports include the SmartBI title, generation timestamp, dataset name, detected domain, applied filters, KPIs, summary tables, and footer. Excel exports include `Summary`, `Analytics`, `Raw Data`, and `Comparison` sheets when applicable.

The API returns `400` for unsupported formats, missing parameters, empty datasets, missing comparison IDs, or filter validation errors, and `404` when the requested upload does not exist.
