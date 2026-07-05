# SmartBI API Documentation

Complete API reference for SmartBI platform.

## Base URL

```
http://localhost:5000/api
```

## Authentication

All API endpoints except `/api/health` and `/api/auth/login` require authentication.

### Login

**Endpoint:** `POST /api/auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful."
}
```

**Response (401 Unauthorized):**
```json
{
  "message": "Invalid credentials."
}
```

### Logout

**Endpoint:** `POST /api/auth/logout`

**Response (200 OK):**
```json
{
  "message": "Logged out."
}
```

## Health Check

**Endpoint:** `GET /api/health`

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "SmartBI"
}
```

## Uploads

### List Uploads

**Endpoint:** `GET /api/uploads/`

**Response (200 OK):**
```json
{
  "items": []
}
```

### Upload Files

**Endpoint:** `POST /api/uploads/`

**Request:** `multipart/form-data`
- `files`: One or multiple Excel files (.xlsx, .xls)

**Response (200 OK):**
```json
{
  "items": [
    {
      "file_name": "sales_data.xlsx",
      "status": "processed",
      "upload_id": 1,
      "domain_name": "Retail Sales",
      "confidence": 0.85,
      "row_count": 150,
      "summary": {},
      "errors": [],
      "warnings": []
    }
  ]
}
```

**Status Values:**
- `processed`: Successfully uploaded and processed
- `validation_failed`: Validation errors found
- `rejected`: Invalid file type
- `error`: Processing error

## Analytics

### Get Summary

**Endpoint:** `GET /api/analytics/summary`

**Query Parameters:**
- `upload_id` (optional): Specific upload ID (defaults to latest)

**Response (200 OK):**
```json
{
  "upload": {
    "id": 1,
    "file_name": "sales_data.xlsx",
    "domain_name": "Retail Sales",
    "confidence": 0.85,
    "row_count": 150,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "domain": {
    "name": "Retail Sales",
    "confidence": 0.85
  },
  "row_count": 150,
  "column_count": 8,
  "kpis": {
    "total_revenue": 125000.50,
    "total_orders": 150,
    "average_order_value": 833.34
  },
  "charts": {
    "primary": {
      "label": "Revenue by Region",
      "labels": ["North", "South", "East", "West"],
      "values": [30000, 40000, 25000, 30000]
    }
  },
  "insights": [
    "Total revenue is ₹125,000.50",
    "South region has highest revenue"
  ]
}
```

### Filter Analytics

**Endpoint:** `GET /api/analytics/filter`

**Query Parameters:**
- `upload_id` (required): Upload ID
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `department` (optional): Filter by department
- `company` (optional): Filter by company
- `category` (optional): Filter by category
- `region` (optional): Filter by region
- `gender` (optional): Filter by gender
- `year` (optional): Filter by year
- `search_keyword` (optional): Text search

**Response (200 OK):**
```json
{
  "upload": {},
  "domain": {},
  "row_count": 50,
  "total_row_count": 150,
  "filtered_row_count": 50,
  "column_count": 8,
  "kpis": {},
  "charts": {},
  "insights": [],
  "filters": {
    "department": "IT",
    "start_date": "2024-01-01"
  }
}
```

### Drill-Down

**Endpoint:** `GET /api/analytics/drilldown`

**Query Parameters:**
- `upload_id` (required): Upload ID
- `field` or `dimension` (required): Field name to drill down
- `value` or `label` (required): Field value to filter
- `metric` or `kpi` (optional): Specific metric name
- `limit` (optional): Results limit (default: 100)
- `offset` (optional): Results offset (default: 0)

**Example:**
```
GET /api/analytics/drilldown?upload_id=1&field=company&value=TechNova&limit=50
```

**Response (200 OK):**
```json
{
  "upload": {},
  "domain": {},
  "drilldown": {
    "field": "company",
    "value": "TechNova",
    "matched_count": 25
  },
  "columns": ["Employee Name", "Department", "Salary"],
  "rows": [
    {
      "Employee Name": "John Doe",
      "Department": "IT",
      "Salary": 75000
    }
  ],
  "analytics": {
    "row_count": 25,
    "column_count": 8,
    "kpis": {},
    "charts": {},
    "insights": []
  }
}
```

### Compare Uploads

**Endpoint:** `GET /api/analytics/compare`

**Query Parameters:**
- `upload_a` (required): First upload ID (baseline)
- `upload_b` (required): Second upload ID (comparison)
- `chart` (optional): Include charts (true/false)
- `summary_only` (optional): Omit detailed analytics (true/false)

**Example:**
```
GET /api/analytics/compare?upload_a=1&upload_b=2&chart=true
```

**Response (200 OK):**
```json
{
  "domain": "Retail Sales",
  "upload_a": {
    "id": 1,
    "file_name": "sales_jan.xlsx",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "upload_b": {
    "id": 2,
    "file_name": "sales_feb.xlsx",
    "created_at": "2024-02-15T10:30:00Z"
  },
  "comparison": {
    "total_revenue": {
      "old": 125000.50,
      "new": 154000.75,
      "difference": 29000.25,
      "growth_percent": 23.20,
      "trend": "Increase"
    },
    "total_orders": {
      "old": 150,
      "new": 180,
      "difference": 30,
      "growth_percent": 20.00,
      "trend": "Increase"
    }
  },
  "charts": {
    "bar_chart": {
      "labels": ["total_revenue", "total_orders"],
      "datasets": [
        {
          "label": "Upload A",
          "data": [125000.50, 150]
        },
        {
          "label": "Upload B",
          "data": [154000.75, 180]
        }
      ]
    },
    "trend_chart": {
      "labels": ["total_revenue", "total_orders"],
      "values": [23.20, 20.00],
      "label": "Growth %"
    }
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "message": "Uploads must have matching domains.",
  "errors": ["upload_a=Retail Sales", "upload_b=HR Management"]
}
```

### Get Domain

**Endpoint:** `GET /api/analytics/domain`

**Query Parameters:**
- `upload_id` (optional): Upload ID

**Response (200 OK):**
```json
{
  "domain": {
    "name": "Retail Sales",
    "confidence": 0.85
  },
  "upload": {
    "id": 1,
    "file_name": "sales_data.xlsx"
  }
}
```

### Get KPIs

**Endpoint:** `GET /api/analytics/kpis`

**Query Parameters:**
- `upload_id` (optional): Upload ID

**Response (200 OK):**
```json
{
  "domain": {
    "name": "Retail Sales",
    "confidence": 0.85
  },
  "kpis": {
    "total_revenue": 125000.50,
    "total_orders": 150,
    "average_order_value": 833.34,
    "top_customers": {
      "Customer A": 5000,
      "Customer B": 4500
    },
    "top_products": {
      "Product X": 10000,
      "Product Y": 8500
    }
  }
}
```

### Get Charts

**Endpoint:** `GET /api/analytics/charts`

**Query Parameters:**
- `upload_id` (optional): Upload ID

**Response (200 OK):**
```json
{
  "domain": {
    "name": "Retail Sales",
    "confidence": 0.85
  },
  "charts": {
    "primary": {
      "label": "Revenue by Region",
      "labels": ["North", "South", "East", "West"],
      "values": [30000, 40000, 25000, 30000]
    },
    "secondary": {
      "label": "Monthly Orders",
      "labels": ["Jan", "Feb", "Mar"],
      "values": [50, 60, 40]
    }
  }
}
```

### Get Dashboard

**Endpoint:** `GET /api/analytics/dashboard`

**Query Parameters:**
- `upload_id` (optional): Upload ID

**Response (200 OK):**
```json
{
  "upload": {},
  "analytics": {
    "domain": {},
    "kpis": {},
    "charts": {},
    "insights": []
  },
  "dashboard": {
    "recent_uploads": [],
    "latest_report": {},
    "dataset_information": {
      "row_count": 150,
      "column_count": 8,
      "source_file": "sales_data.xlsx"
    },
    "domain_detection": {},
    "last_refresh_time": "2024-01-15T10:30:00Z",
    "record_count": 150
  }
}
```

### Get Latest Upload

**Endpoint:** `GET /api/analytics/latest`

**Response (200 OK):**
```json
{
  "item": {
    "id": 1,
    "file_name": "sales_data.xlsx",
    "domain_name": "Retail Sales",
    "confidence": 0.85,
    "row_count": 150,
    "summary_json": {},
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## Reports

### Report Metadata

**Endpoint:** `GET /api/reports/`

**Response (200 OK):**
```json
{
  "message": "Reports endpoint",
  "title": "SmartBI Report",
  "available_formats": ["pdf", "excel", "csv", "json"],
  "download_endpoint": "/api/reports/download",
  "parameters": {
    "required": ["upload_id", "format"],
    "optional": ["compare", "upload_b", "filter parameters"]
  }
}
```

### Download Report

**Endpoint:** `GET /api/reports/download`

**Query Parameters:**
- `upload_id` (required): Upload ID
- `format` (required): Report format (`pdf`, `excel`, `xlsx`, `csv`, `json`)
- `compare` (optional): Include comparison (true/false)
- `upload_b` (optional): Second upload ID for comparison
- Filter parameters (optional): Same as `/api/analytics/filter`

**Examples:**

Basic report:
```
GET /api/reports/download?upload_id=1&format=pdf
```

Filtered report:
```
GET /api/reports/download?upload_id=1&format=excel&department=IT&start_date=2024-01-01
```

Comparison report:
```
GET /api/reports/download?upload_id=1&format=csv&compare=true&upload_b=2
```

**Response (200 OK):**
- Binary file content with appropriate MIME type
- `Content-Disposition` header with filename

**Error Response (400 Bad Request):**
```json
{
  "message": "Unsupported report format.",
  "errors": ["invalid_format"]
}
```

## History

### Get Upload History

**Endpoint:** `GET /api/history/uploads`

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 2,
      "file_name": "sales_feb.xlsx",
      "domain_name": "Retail Sales",
      "confidence": 0.82,
      "row_count": 180,
      "summary_json": {},
      "created_at": "2024-02-15T10:30:00Z"
    },
    {
      "id": 1,
      "file_name": "sales_jan.xlsx",
      "domain_name": "Retail Sales",
      "confidence": 0.85,
      "row_count": 150,
      "summary_json": {},
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Error Responses

### 400 Bad Request

```json
{
  "message": "Invalid filter parameters.",
  "errors": ["start_date must be in YYYY-MM-DD format"]
}
```

### 401 Unauthorized

```json
{
  "message": "Authentication required."
}
```

### 404 Not Found

```json
{
  "message": "Resource not found.",
  "details": "Upload not found"
}
```

### 500 Internal Server Error

```json
{
  "message": "Internal server error.",
  "details": "Database connection failed"
}
```

## Rate Limiting

No rate limiting implemented. Consider adding rate limiting in production.

## Pagination

Pagination is available for drill-down endpoint:
- `limit`: Results per page (default: 100, max: 1000)
- `offset`: Skip N results (default: 0)

## CORS

CORS is not configured by default. Add Flask-CORS for cross-origin requests:

```python
from flask_cors import CORS
CORS(app)
```

## Webhook Support

Not implemented. Consider adding webhooks for:
- Upload completion
- Processing completion
- Report generation

## WebSocket Support

Not implemented. Consider adding WebSocket for:
- Real-time upload progress
- Live dashboard updates

## API Versioning

Current version: v1 (implicit)

Future versions could use:
- URL versioning: `/api/v2/analytics/summary`
- Header versioning: `Accept: application/vnd.smartbi.v2+json`

## Best Practices

1. **Always authenticate** before calling protected endpoints
2. **Handle errors gracefully** with proper status code checks
3. **Use appropriate HTTP methods** (GET for read, POST for write)
4. **Include query parameters** for filtering and pagination
5. **Cache responses** when appropriate to reduce server load
6. **Validate inputs** before sending requests
7. **Use HTTPS** in production
8. **Store session cookies** securely

## Code Examples

### Python (requests)

```python
import requests

# Login
session = requests.Session()
response = session.post('http://localhost:5000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})

# Upload file
files = {'files': open('sales.xlsx', 'rb')}
response = session.post('http://localhost:5000/api/uploads/', files=files)
print(response.json())

# Get analytics
response = session.get('http://localhost:5000/api/analytics/summary?upload_id=1')
print(response.json())
```

### JavaScript (Fetch)

```javascript
// Login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  credentials: 'same-origin',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});

// Upload file
const formData = new FormData();
formData.append('files', fileInput.files[0]);
const uploadResponse = await fetch('/api/uploads/', {
  method: 'POST',
  credentials: 'same-origin',
  body: formData
});

// Get analytics
const analyticsResponse = await fetch('/api/analytics/summary?upload_id=1', {
  credentials: 'same-origin'
});
const data = await analyticsResponse.json();
```

### cURL

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c cookies.txt

# Upload file
curl -X POST http://localhost:5000/api/uploads/ \
  -b cookies.txt \
  -F "files=@sales.xlsx"

# Get analytics
curl http://localhost:5000/api/analytics/summary?upload_id=1 \
  -b cookies.txt
```

---

For additional information, see [README.md](README.md) and [USER_MANUAL.md](USER_MANUAL.md).
