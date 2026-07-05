# SmartBI Project Structure

Complete overview of the SmartBI codebase organization and architecture.

## Directory Tree

```
SmartBI/
├── backend/                      # Backend application
│   ├── app/                      # Main application package
│   │   ├── blueprints/           # Flask blueprints (route handlers)
│   │   │   ├── analytics.py      # Analytics API endpoints
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── history.py        # Upload history endpoints
│   │   │   ├── reports.py        # Report generation endpoints
│   │   │   └── uploads.py        # File upload endpoints
│   │   ├── services/             # Business logic layer
│   │   │   ├── analytics/        # Analytics engine
│   │   │   │   ├── __init__.py
│   │   │   │   ├── attendance.py # Student attendance analytics
│   │   │   │   ├── common.py     # Shared analytics utilities
│   │   │   │   ├── dispatcher.py # Domain-based routing
│   │   │   │   ├── engine.py     # Main analytics engine
│   │   │   │   ├── generic.py    # Generic domain analytics
│   │   │   │   ├── hr.py         # HR analytics
│   │   │   │   ├── inventory.py  # Inventory analytics
│   │   │   │   ├── placement.py  # Placement analytics
│   │   │   │   └── sales.py      # Retail sales analytics
│   │   │   ├── analytics_service.py    # Analytics calculations
│   │   │   ├── auth_service.py         # Authentication logic
│   │   │   ├── comparison_service.py   # Dataset comparison
│   │   │   ├── database_service.py     # Database operations
│   │   │   ├── domain_service.py       # Domain detection
│   │   │   ├── drilldown_service.py    # Drill-down logic
│   │   │   ├── excel_service.py        # Excel processing
│   │   │   ├── file_service.py         # File operations
│   │   │   ├── filter_service.py       # Data filtering
│   │   │   ├── processing_service.py   # Upload processing
│   │   │   ├── report_service.py       # Report generation
│   │   │   └── validation_service.py   # Data validation
│   │   ├── __init__.py           # Flask app factory
│   │   ├── config.py             # Configuration class
│   │   └── extensions.py         # Logging initialization
│   ├── tests/                    # Test suite
│   │   ├── conftest.py           # Pytest configuration
│   │   ├── test_analytics_api.py
│   │   ├── test_analytics_engine.py
│   │   ├── test_auth_and_api.py
│   │   ├── test_comparison_api.py
│   │   ├── test_dashboard_api.py
│   │   ├── test_domain_and_analytics.py
│   │   ├── test_drilldown_api.py
│   │   ├── test_filter_api.py
│   │   ├── test_processing_service.py
│   │   ├── test_reports_api.py
│   │   ├── test_upload_workflow.py
│   │   └── test_validation_service.py
│   └── README.md                 # Backend documentation
├── frontend/                     # Frontend application
│   ├── assets/                   # Static assets
│   │   ├── api.js                # API client utilities
│   │   ├── app.js                # Main application logic
│   │   ├── charts.js             # Chart rendering utilities
│   │   ├── dashboard.js          # Dashboard page logic
│   │   ├── filters.js            # Filter management
│   │   ├── history.js            # History page logic
│   │   ├── styles.css            # Application styles
│   │   ├── tables.js             # Table utilities
│   │   └── utils.js              # Helper functions
│   ├── pages/                    # HTML pages
│   │   ├── dashboard.html        # Dashboard page
│   │   ├── history.html          # Upload history page
│   │   ├── reports.html          # Reports page
│   │   └── upload.html           # Upload page
│   ├── index.html                # Landing page
│   └── README.md                 # Frontend documentation
├── sql/                          # Database scripts
│   ├── powerbi_views.sql         # Power BI reporting views
│   ├── schema.sql                # Database schema
│   └── README.md                 # SQL documentation
├── powerbi/                      # Power BI resources
│   ├── POWER_BI_GUIDE.md         # Power BI integration guide
│   └── README.md                 # Power BI documentation
├── documentation/                # Additional documentation
│   ├── screenshots/              # Application screenshots
│   │   └── README.md
│   ├── README.md
│   └── setup.md                  # Setup guide
├── sample_data/                  # Sample datasets
│   ├── generated/                # Generated sample files
│   │   ├── attendance_sample.xlsx
│   │   ├── hr_sample.xlsx
│   │   ├── inventory_sample.xlsx
│   │   ├── placement_sample.xlsx
│   │   └── retail_sales_sample.xlsx
│   └── generate_sample_excels.py # Sample generator script
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── API_DOCUMENTATION.md          # API reference
├── CHANGELOG.md                  # Version history
├── DEPLOYMENT.md                 # Deployment guide
├── LICENSE                       # MIT License
├── README.md                     # Main documentation
├── SECURITY.md                   # Security policy
├── requirements.txt              # Python dependencies
└── run.py                        # Application entry point
```

## Architecture Overview

### Three-Tier Architecture

```
┌─────────────────────────────────────┐
│          Presentation Layer         │
│  (Frontend - HTML/CSS/JavaScript)   │
└─────────────┬───────────────────────┘
              │ HTTP/AJAX
┌─────────────▼───────────────────────┐
│         Application Layer           │
│  (Flask Blueprints + Services)      │
└─────────────┬───────────────────────┘
              │ SQL Queries
┌─────────────▼───────────────────────┐
│           Data Layer                │
│    (PostgreSQL + JSONB Storage)     │
└─────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. Presentation Layer (Frontend)
- User interface rendering
- Client-side validation
- API communication
- Chart visualization
- Event handling

#### 2. Application Layer (Backend)
- Request routing (Blueprints)
- Business logic (Services)
- Authentication/Authorization
- Data transformation
- Error handling

#### 3. Data Layer (Database)
- Data persistence
- Query optimization
- JSONB storage for flexibility
- SQL views for reporting

## Backend Components

### Flask App Factory Pattern

```python
# app/__init__.py
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    # ...
    
    return app
```

### Blueprint Architecture

Each blueprint handles a specific domain:

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| auth_bp | /api/auth | Authentication (login/logout) |
| uploads_bp | /api/uploads | File upload and processing |
| analytics_bp | /api/analytics | Analytics and insights |
| reports_bp | /api/reports | Report generation |
| history_bp | /api/history | Upload history |

### Service Layer Pattern

Services contain reusable business logic:

```
Services
├── Authentication (auth_service.py)
├── Database Operations (database_service.py)
├── File Operations (file_service.py)
├── Excel Processing (excel_service.py)
├── Domain Detection (domain_service.py)
├── Data Validation (validation_service.py)
├── Data Cleaning (processing_service.py)
├── Analytics Engine (analytics/)
├── Filtering (filter_service.py)
├── Drill-Down (drilldown_service.py)
├── Comparison (comparison_service.py)
└── Reporting (report_service.py)
```

### Analytics Engine Architecture

```
analytics/
├── engine.py          # Main entry point
├── dispatcher.py      # Routes to domain-specific modules
├── common.py          # Shared utilities
├── placement.py       # Placement domain
├── hr.py              # HR domain
├── sales.py           # Sales domain
├── inventory.py       # Inventory domain
├── attendance.py      # Attendance domain
└── generic.py         # Generic domain
```

Each domain module provides:
- `analyze(rows)` - Main analysis function
- `calculate_kpis(rows)` - KPI calculations
- `build_charts(rows)` - Chart data generation
- `generate_insights(kpis)` - Insight generation

## Frontend Components

### JavaScript Modules

| Module | Purpose |
|--------|---------|
| api.js | API communication utilities |
| app.js | Main application initialization |
| charts.js | Chart.js rendering |
| dashboard.js | Dashboard logic |
| filters.js | Filter management |
| history.js | History page logic |
| tables.js | Table utilities |
| utils.js | Helper functions |

### Page Structure

```
Frontend Pages
├── index.html        # Landing/login page
├── upload.html       # File upload interface
├── dashboard.html    # Analytics dashboard
├── reports.html      # Report generation
└── history.html      # Upload history
```

### CSS Organization

```css
/* styles.css structure */
:root { /* CSS variables */ }
* { /* Reset styles */ }
body { /* Base styles */ }
.shell { /* Layout container */ }
.sidebar { /* Navigation sidebar */ }
.hero { /* Main content area */ }
.button { /* Button styles */ }
.kpi-card { /* KPI card styles */ }
/* ... more component styles */
```

## Database Schema

### Core Tables

```sql
-- Uploads metadata
smartbi_uploads (
    id BIGSERIAL PRIMARY KEY,
    file_name TEXT,
    domain_name TEXT,
    confidence NUMERIC,
    row_count INTEGER,
    summary_json JSONB,
    created_at TIMESTAMPTZ
)

-- Cleaned data rows
smartbi_clean_rows (
    id BIGSERIAL PRIMARY KEY,
    upload_id BIGINT REFERENCES smartbi_uploads,
    row_number INTEGER,
    row_data JSONB,
    created_at TIMESTAMPTZ
)
```

### Indexes

```sql
-- Performance indexes
idx_smartbi_uploads_created_at
idx_smartbi_uploads_domain_created_at
idx_smartbi_clean_rows_upload_id
idx_smartbi_clean_rows_upload_row_number
idx_smartbi_clean_rows_row_data_gin
```

### Power BI Views

30+ reporting views including:
- `v_smartbi_upload_summary`
- `v_smartbi_rows_flat`
- `v_smartbi_kpis`
- Domain-specific views (placement, hr, sales, inventory, attendance)
- Summary aggregation views

## Data Flow

### Upload Flow

```
1. User uploads Excel file(s)
   ↓
2. uploads_bp receives file
   ↓
3. file_service saves to disk
   ↓
4. excel_service reads and parses
   ↓
5. validation_service validates data
   ↓
6. domain_service detects domain
   ↓
7. processing_service cleans data
   ↓
8. analytics/engine analyzes data
   ↓
9. database_service stores to PostgreSQL
   ↓
10. Response sent to frontend
```

### Analytics Flow

```
1. Frontend requests analytics
   ↓
2. analytics_bp handles request
   ↓
3. database_service fetches data
   ↓
4. filter_service applies filters (optional)
   ↓
5. analytics/engine processes data
   ↓
6. Domain-specific module calculates KPIs
   ↓
7. Charts and insights generated
   ↓
8. JSON response returned
   ↓
9. Frontend renders visualizations
```

### Report Generation Flow

```
1. User requests report
   ↓
2. reports_bp handles request
   ↓
3. database_service fetches data
   ↓
4. filter_service applies filters
   ↓
5. report_service generates file
   ↓
6. Format-specific generator (PDF/Excel/CSV/JSON)
   ↓
7. Binary file returned
   ↓
8. Browser downloads file
```

## Configuration Management

### Environment Variables

```
.env file
├── SMARTBI_SECRET_KEY          # Flask secret key
├── SMARTBI_DATABASE_URL        # PostgreSQL connection
├── SMARTBI_ADMIN_USERNAME      # Admin username
├── SMARTBI_ADMIN_PASSWORD      # Admin password
├── SMARTBI_UPLOAD_FOLDER       # Upload directory
├── SMARTBI_CLEANED_FOLDER      # Cleaned files directory
├── SMARTBI_PROCESSED_FOLDER    # Processed files directory
├── SMARTBI_ORIGINAL_FOLDER     # Original files directory
└── SMARTBI_MAX_UPLOAD_BYTES    # Max upload size
```

### Config Class

```python
# app/config.py
class Config:
    SECRET_KEY = os.getenv('SMARTBI_SECRET_KEY', 'default')
    DATABASE_URL = os.getenv('SMARTBI_DATABASE_URL')
    # ... more configuration
```

## Testing Structure

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_auth_and_api.py     # Auth + basic API tests
├── test_upload_workflow.py  # Upload integration tests
├── test_validation_service.py  # Validation tests
├── test_domain_and_analytics.py  # Domain detection + analytics
├── test_analytics_engine.py  # Analytics engine tests
├── test_analytics_api.py    # Analytics API tests
├── test_filter_api.py       # Filtering tests
├── test_drilldown_api.py    # Drill-down tests
├── test_comparison_api.py   # Comparison tests
├── test_reports_api.py      # Report generation tests
├── test_dashboard_api.py    # Dashboard API tests
└── test_processing_service.py  # Processing tests
```

### Test Categories

- **Unit Tests**: Individual functions and classes
- **Integration Tests**: Multi-component workflows
- **API Tests**: HTTP endpoint testing
- **Service Tests**: Business logic validation

## Coding Conventions

### Python Style
- PEP 8 compliance
- Type hints with `from __future__ import annotations`
- Dataclasses for DTOs
- Docstrings for public APIs
- Context managers for resources

### JavaScript Style
- ES6+ syntax
- Async/await for promises
- Modular organization
- Descriptive variable names
- Comments for complex logic

### SQL Style
- Lowercase keywords (readability preference)
- Parameterized queries always
- Indexes for performance
- Views for abstraction

## File Organization Principles

1. **Separation of Concerns**: Blueprints, services, models
2. **Single Responsibility**: Each module has one clear purpose
3. **DRY (Don't Repeat Yourself)**: Shared utilities in common modules
4. **Explicit Dependencies**: Clear import structure
5. **Test Co-location**: Tests mirror source structure

## Extension Points

### Adding a New Domain

1. Create `app/services/analytics/new_domain.py`
2. Implement `analyze(rows)` function
3. Add to `dispatcher.py` DOMAIN_MAP
4. Add keywords to `domain_service.py`
5. Create Power BI views in SQL
6. Add tests

### Adding a New API Endpoint

1. Add route to appropriate blueprint
2. Implement business logic in service
3. Add authentication decorator
4. Document in API_DOCUMENTATION.md
5. Add tests

### Adding a New Report Format

1. Add to `SUPPORTED_FORMATS` in `report_service.py`
2. Implement `_build_FORMAT_report()` function
3. Handle MIME type and filename
4. Add tests

---

For detailed implementation guides, see:
- [README.md](README.md)
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
