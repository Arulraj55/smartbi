# SmartBI - Smart Business Intelligence Platform

![SmartBI](https://img.shields.io/badge/SmartBI-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.13-green)
![Flask](https://img.shields.io/badge/Flask-3.1.3-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-orange)

SmartBI is an intelligent business analytics platform that automatically detects business domains from Excel uploads, validates and cleans data, generates insightful analytics, and provides Power BI-ready SQL views for advanced reporting.

## Features

- **Automatic Domain Detection**: Identifies business context (Placement, HR, Sales, Inventory, Attendance, Generic) from column names
- **Excel Upload & Validation**: Multi-file upload with comprehensive validation and data quality checks
- **Data Cleaning**: Automated data cleaning and normalization with PostgreSQL storage
- **Analytics Engine**: Domain-specific KPIs, charts, and insights generation
- **Interactive Dashboard**: Real-time visualization with Chart.js
- **Advanced Filtering**: Dynamic data filtering with multiple criteria
- **Drill-Down Analysis**: Deep-dive into specific metrics and dimensions
- **Historical Comparison**: Compare two datasets from the same domain
- **Report Generation**: Export reports in PDF, Excel, CSV, and JSON formats
- **Power BI Integration**: Pre-built SQL views for seamless Power BI connectivity
- **Authentication**: Secure admin authentication system
- **Upload History**: Track and manage all uploaded datasets

## Technology Stack

### Backend
- **Framework**: Flask 3.1.3
- **Database**: PostgreSQL (Neon serverless)
- **Data Processing**: pandas 3.0.3, openpyxl 3.1.5
- **PDF Generation**: ReportLab 4.4.6
- **Testing**: pytest 9.1.1

### Frontend
- **HTML5 / CSS3**: Modern, responsive design
- **JavaScript**: Vanilla JS, no framework dependencies
- **Visualization**: Chart.js for interactive charts
- **API Communication**: Fetch API with async/await

### Database
- **PostgreSQL 15+**: Neon serverless database
- **JSONB Storage**: Flexible schema for multi-domain data
- **Optimized Indexes**: Performance-tuned queries
- **SQL Views**: Power BI-ready reporting layer

## Project Structure

```
SmartBI/
├── backend/
│   ├── app/
│   │   ├── blueprints/          # API route handlers
│   │   ├── services/            # Business logic layer
│   │   │   └── analytics/       # Domain-specific analytics
│   │   ├── config.py            # Application configuration
│   │   ├── extensions.py        # Logging setup
│   │   └── __init__.py          # Flask app factory
│   ├── tests/                   # Comprehensive test suite
│   └── README.md
├── frontend/
│   ├── assets/                  # JavaScript and CSS files
│   ├── pages/                   # HTML pages
│   └── index.html               # Landing page
├── sql/
│   ├── schema.sql               # Database schema
│   └── powerbi_views.sql        # Power BI reporting views
├── powerbi/
│   └── POWER_BI_GUIDE.md        # Power BI integration guide
├── documentation/
│   ├── screenshots/
│   └── setup.md
├── sample_data/                 # Sample Excel files
├── .env.example                 # Environment template
├── .gitignore
├── requirements.txt
└── run.py                       # Application entry point
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database (Neon recommended)
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartbi.git
   cd smartbi
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database**
   ```bash
   # Run schema.sql and powerbi_views.sql on your PostgreSQL database
   psql -h your-host -U your-user -d smartbi -f sql/schema.sql
   psql -h your-host -U your-user -d smartbi -f sql/powerbi_views.sql
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   ```
   http://localhost:5000
   ```

### Default Credentials

```
Username: admin
Password: admin123
```

**IMPORTANT**: Change these credentials in production!

## Configuration

Edit `.env` file with your settings:

```env
SMARTBI_SECRET_KEY=your-secret-key-here
SMARTBI_DATABASE_URL=postgresql://user:pass@host:port/database
SMARTBI_ADMIN_USERNAME=admin
SMARTBI_ADMIN_PASSWORD=secure-password
SMARTBI_UPLOAD_FOLDER=backend/uploads
SMARTBI_CLEANED_FOLDER=backend/cleaned
SMARTBI_PROCESSED_FOLDER=backend/processed
SMARTBI_ORIGINAL_FOLDER=backend/original
SMARTBI_MAX_UPLOAD_BYTES=26214400
```

## Usage

### 1. Upload Excel Files

- Navigate to **Upload** page
- Select one or multiple Excel files (.xlsx, .xls)
- Click **Upload**
- System automatically detects domain and validates data

### 2. View Analytics

- Navigate to **Dashboard** page
- View KPIs, charts, and insights
- Apply filters to narrow down data
- Drill down into specific metrics

### 3. Generate Reports

- Navigate to **Reports** page
- Select upload and format (PDF/Excel/CSV/JSON)
- Apply filters if needed
- Download report

### 4. Compare Datasets

- Use comparison API endpoint
- Select two uploads from the same domain
- View growth metrics and trends

## API Documentation

### Authentication

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

### Upload Files

```http
POST /api/uploads/
Content-Type: multipart/form-data
Cookie: session=xxx

files: [file1.xlsx, file2.xlsx]
```

### Analytics

```http
GET /api/analytics/summary?upload_id=1
GET /api/analytics/filter?upload_id=1&department=CSE
GET /api/analytics/drilldown?upload_id=1&field=company&value=TechNova
GET /api/analytics/compare?upload_a=1&upload_b=2&chart=true
```

### Reports

```http
GET /api/reports/download?upload_id=1&format=pdf
GET /api/reports/download?upload_id=1&format=excel&department=IT
GET /api/reports/download?upload_id=1&format=csv&compare=true&upload_b=2
```

For complete API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## Supported Domains

| Domain | Detected Columns | Key KPIs |
|--------|-----------------|----------|
| **Placement Management** | Candidate, Company, Package, CTC | Placement %, Avg Package, Top Companies |
| **HR Management** | Employee, Department, Salary | Employee Count, Avg Salary, Attendance |
| **Retail Sales** | Order, Customer, Revenue, Amount | Total Revenue, Orders, Top Products |
| **Inventory** | Product, Stock, SKU, Quantity | Stock Value, Low Stock, Out of Stock |
| **Student Attendance** | Student, Class, Present, Absent | Attendance %, Class Performance |
| **Generic** | Any columns | Row Count, Column Count, Data Quality |

## Testing

Run the test suite:

```bash
cd backend
python -m pytest tests/ -v
```

Test coverage:

```bash
python -m pytest tests/ --cov=app --cov-report=html
```

## Deployment

### Local Deployment

Follow the Quick Start instructions above.

### Neon PostgreSQL Setup

1. Create a free account at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string
4. Update `SMARTBI_DATABASE_URL` in `.env`
5. Run `schema.sql` and `powerbi_views.sql`

### Render Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### Docker Deployment

```bash
docker build -t smartbi .
docker run -p 5000:5000 --env-file .env smartbi
```

## Power BI Integration

SmartBI provides pre-built SQL views for Power BI:

1. Open Power BI Desktop
2. Get Data > PostgreSQL
3. Enter Neon connection details
4. Load `v_smartbi_*` views
5. Build reports using provided DAX measures

See [powerbi/POWER_BI_GUIDE.md](powerbi/POWER_BI_GUIDE.md) for complete guide.

## Security

- Session-based authentication
- SQL injection prevention with parameterized queries
- XSS protection with input sanitization
- File upload validation
- Environment variable configuration
- Secure password hashing recommended for production

See [SECURITY.md](SECURITY.md) for detailed security guidelines.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Email: support@smartbi.example.com
- Documentation: [documentation/](documentation/)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Acknowledgments

- Flask framework
- Chart.js library
- Neon PostgreSQL
- ReportLab PDF generation
- pandas data processing

---

**SmartBI** - Transforming Excel data into business intelligence
