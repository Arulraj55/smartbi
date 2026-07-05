# SmartBI Power BI Guide

This guide explains how to build a professional SmartBI report in Power BI Desktop from the PostgreSQL/Neon database. Do not generate or commit a `.pbix` automatically; build it manually from the SQL views in `sql/powerbi_views.sql`.

## 1. Database Connection

1. Open Power BI Desktop.
2. Select `Get data` > `PostgreSQL database`.
3. Enter the Neon host and database name from `DATABASE_URL`.
4. Choose `Import` mode for the first version of the report.
5. Authenticate with the Neon reporting user.
6. Select the required `v_smartbi_*` views.
7. Load the views and confirm column types.

Use a read-only Neon user for Power BI whenever possible. Do not embed admin database credentials in shared PBIX files.

## 2. Required SQL Views

Core views:

- `v_smartbi_upload_summary`: upload dimension and upload-level metadata.
- `v_smartbi_rows_flat`: row-level cleaned dataset facts with upload metadata.
- `v_smartbi_kpis`: domain-level upload summary.
- `v_smartbi_latest_rows`: backward-compatible raw row explorer view.
- `v_smartbi_domain_upload_monthly`: upload and row counts by domain/month.

Placement:

- `v_smartbi_placement_rows`
- `v_smartbi_placement_summary`
- `v_smartbi_placement_company_summary`
- `v_smartbi_placement_department_summary`
- `v_smartbi_placement_monthly`

HR:

- `v_smartbi_hr_rows`
- `v_smartbi_hr_summary`
- `v_smartbi_hr_monthly`

Sales:

- `v_smartbi_sales_rows`
- `v_smartbi_sales_summary`
- `v_smartbi_sales_monthly_revenue`
- `v_smartbi_sales_region_summary`
- `v_smartbi_sales_monthly`

Inventory:

- `v_smartbi_inventory_rows`
- `v_smartbi_inventory_summary`
- `v_smartbi_inventory_monthly`

Attendance:

- `v_smartbi_attendance_rows`
- `v_smartbi_attendance_summary`
- `v_smartbi_attendance_monthly`

Generic:

- `v_smartbi_generic_rows`
- `v_smartbi_generic_summary`
- `v_smartbi_generic_monthly`

## 3. Recommended Data Model

The existing application schema is sufficient for flexible uploads because it stores cleaned records as JSONB. For Power BI, use the SQL views as a semantic reporting layer. For long-term reporting at larger scale, a star schema is recommended.

Recommended model:

| Table/View | Role | Primary Key | Foreign Key | Notes |
| --- | --- | --- | --- | --- |
| `v_smartbi_upload_summary` | Dimension | `upload_id` | None | Upload slicer, domain, date, file metadata |
| Domain row views | Fact | `clean_row_id` | `upload_id` | One row per cleaned business record |
| Domain summary views | Aggregate fact | `upload_id` | `upload_id` | KPI pages and comparison cards |
| `v_smartbi_domain_upload_monthly` | Aggregate fact | domain/month composite | None | Executive trends |
| Date table | Dimension | `Date` | upload/date fields | Create in Power BI |

Relationships:

- `v_smartbi_upload_summary[upload_id]` 1-to-many to each domain row view `[upload_id]`.
- `v_smartbi_upload_summary[upload_id]` 1-to-many to each domain summary view `[upload_id]`.
- Date table `Date[Date]` 1-to-many to view date fields such as `[upload_date]` or `[month]`.
- Filtering direction: single direction from dimensions to facts.
- Cardinality: one-to-many from upload/date dimensions to facts.

Recommended star-schema improvement:

- Keep `smartbi_uploads` as `dim_upload`.
- Add generated domain fact tables later, such as `fact_sales_order`, `fact_placement_candidate`, `fact_inventory_snapshot`, and `fact_attendance_record`.
- Add shared dimensions such as `dim_date`, `dim_department`, `dim_company`, `dim_product`, `dim_region`, and `dim_student_employee`.
- Continue using JSONB raw storage as the ingestion audit layer.

## 4. DAX Measures

Create a Date table:

```DAX
Date =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2020, 1, 1 ), DATE ( 2035, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Month Number", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "YYYY-MM" ),
    "Quarter", "Q" & FORMAT ( [Date], "Q" )
)
```

Core measures:

```DAX
Total Uploads = DISTINCTCOUNT ( v_smartbi_upload_summary[upload_id] )
Total Rows = SUM ( v_smartbi_upload_summary[row_count] )
Average Confidence = AVERAGE ( v_smartbi_upload_summary[confidence] )
```

Sales:

```DAX
Revenue = SUM ( v_smartbi_sales_summary[revenue] )
Orders = SUM ( v_smartbi_sales_summary[orders] )
Average Order Value = DIVIDE ( [Revenue], [Orders] )
Revenue Growth % =
VAR PreviousRevenue = CALCULATE ( [Revenue], DATEADD ( 'Date'[Date], -1, MONTH ) )
RETURN DIVIDE ( [Revenue] - PreviousRevenue, PreviousRevenue )
Running Revenue = CALCULATE ( [Revenue], FILTER ( ALLSELECTED ( 'Date'[Date] ), 'Date'[Date] <= MAX ( 'Date'[Date] ) ) )
Revenue YoY % =
VAR PriorYear = CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
RETURN DIVIDE ( [Revenue] - PriorYear, PriorYear )
Revenue MoM % =
VAR PriorMonth = CALCULATE ( [Revenue], DATEADD ( 'Date'[Date], -1, MONTH ) )
RETURN DIVIDE ( [Revenue] - PriorMonth, PriorMonth )
Revenue Moving Average 3M = AVERAGEX ( DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -3, MONTH ), [Revenue] )
```

Placement:

```DAX
Total Students = SUM ( v_smartbi_placement_summary[total_students] )
Placed Students = SUM ( v_smartbi_placement_summary[placed_students] )
Placement % = DIVIDE ( [Placed Students], [Total Students] )
Average Package = AVERAGE ( v_smartbi_placement_summary[average_package] )
Highest Package = MAX ( v_smartbi_placement_summary[highest_package] )
Company Rank = RANKX ( ALLSELECTED ( v_smartbi_placement_company_summary[company] ), [Placed Students], , DESC )
```

HR:

```DAX
Employees = SUM ( v_smartbi_hr_summary[employees] )
Departments = SUM ( v_smartbi_hr_summary[departments] )
Average Salary = AVERAGE ( v_smartbi_hr_summary[average_salary] )
HR Attendance % = AVERAGE ( v_smartbi_hr_summary[attendance_percentage] ) / 100
Attrition Count = SUM ( v_smartbi_hr_summary[attrition_count] )
```

Inventory:

```DAX
Products = SUM ( v_smartbi_inventory_summary[products] )
Stock Value = SUM ( v_smartbi_inventory_summary[stock_value] )
Low Stock Items = SUM ( v_smartbi_inventory_summary[low_stock] )
Out Of Stock Items = SUM ( v_smartbi_inventory_summary[out_of_stock] )
Supplier Count = SUM ( v_smartbi_inventory_summary[suppliers] )
```

Attendance:

```DAX
Attendance Rows = SUM ( v_smartbi_attendance_summary[attendance_rows] )
Present Count = SUM ( v_smartbi_attendance_summary[present_count] )
Absent Count = SUM ( v_smartbi_attendance_summary[absent_count] )
Attendance % = DIVIDE ( [Present Count], [Attendance Rows] )
```

Top N and ranking pattern:

```DAX
Top N Revenue =
IF (
    RANKX ( ALLSELECTED ( v_smartbi_sales_region_summary[region] ), [Revenue], , DESC ) <= 10,
    [Revenue]
)
```

## 5. Dashboard Pages

### Page 1: Executive Summary

Visuals:

- Cards: total uploads, total rows, latest upload, average confidence.
- Bar chart: rows by domain.
- Line chart: uploads by month.
- Treemap: domain contribution.
- Table: latest uploads.
- Decomposition Tree: total rows by domain, upload, file.

### Page 2: Placement Analytics

Visuals:

- Cards: total students, placed students, placement %, average package, highest package.
- Bar chart: company-wise placements.
- Matrix: department by company.
- Pie chart: gender distribution.
- Scatter: package by department/company.
- Table: candidate drill-through details.

### Page 3: HR Analytics

Visuals:

- Cards: employees, departments, average salary, attendance %, attrition count.
- Bar chart: employees by department.
- Area chart: HR upload trend.
- Matrix: department salary and attendance.
- Gauge: attendance %.
- Waterfall: attrition impact by department.

### Page 4: Sales Analytics

Visuals:

- Cards: revenue, orders, average order value, customers, products.
- Line chart: monthly revenue.
- Bar chart: region revenue.
- Treemap: product/category revenue.
- Map: revenue by region/state/city when location data is available.
- Waterfall: revenue change by month.

### Page 5: Inventory Analytics

Visuals:

- Cards: products, stock value, low stock, out of stock, suppliers.
- Bar chart: stock by category.
- Matrix: product by supplier.
- Gauge: low-stock ratio.
- Treemap: supplier distribution.
- Table: low-stock items.

### Page 6: Attendance Analytics

Visuals:

- Cards: attendance %, present count, absent count, classes, subjects.
- Line chart: monthly attendance.
- Bar chart: class performance.
- Matrix: subject by class.
- Gauge: attendance %.
- Table: student attendance records.

### Page 7: Historical Comparison

Visuals:

- Cards: selected old/new upload names.
- Bar chart: KPI old vs new.
- Waterfall: KPI difference.
- Line chart: KPI trend over upload month.
- Matrix: old, new, difference, growth %, trend.
- Decomposition Tree: growth by domain and metric.

### Page 8: Dataset Explorer

Visuals:

- Table: `v_smartbi_latest_rows` JSON row explorer.
- Matrix: uploads by domain and month.
- Cards: selected upload row count, domain, confidence.
- Slicers: upload, domain, date, department/company/category/region where applicable.

## 6. Slicers

Recommended slicers:

- Date: from Date table.
- Department: placement and HR row views.
- Company: placement row view.
- Category: sales and inventory row views.
- Region: sales row view.
- Gender: placement and HR row views.
- Year: upload year or Date table year.
- Upload: `v_smartbi_upload_summary[file_name]` or `[upload_id]`.
- Domain: `v_smartbi_upload_summary[domain_name]`.

Use single-select upload slicers for historical comparison pages when old/new upload logic is modeled in separate duplicated upload tables or disconnected slicer tables.

## 7. Refresh Strategy

Import mode is recommended first because:

- Uploaded datasets are already cleaned and stored.
- Import mode gives faster visuals and richer DAX behavior.
- Neon free and serverless tiers can pause or throttle frequent DirectQuery workloads.

DirectQuery may be suitable when:

- Datasets become too large for import.
- Near-real-time reporting is required.
- Neon compute is provisioned for BI concurrency.

Refresh process:

1. Publish the PBIX to Power BI Service.
2. Configure PostgreSQL credentials with the read-only Neon user.
3. Install/configure an on-premises data gateway only if the database is not directly reachable from Power BI Service.
4. Schedule refresh based on upload frequency.
5. Refresh after new SmartBI uploads are processed.

Security:

- Use read-only credentials.
- Restrict Neon IP access where possible.
- Do not expose `DATABASE_URL` in report pages or documentation screenshots.
- Consider Power BI Row-Level Security if reports are shared across departments.

## 8. Troubleshooting

Connection fails:

- Confirm Neon host, database, username, password, and SSL requirement.
- Confirm the Power BI PostgreSQL connector is installed and current.

Views are missing:

- Run `sql/schema.sql` first.
- Run `sql/powerbi_views.sql` after schema creation.
- Confirm the connected user has `select` access to the views.

Numeric fields are blank:

- Source Excel values may contain currency symbols or non-numeric text.
- Clean the dataset before upload or extend the SQL view alias list for that column.

Relationships are ambiguous:

- Keep filter direction single.
- Use `v_smartbi_upload_summary` as the upload dimension.
- Avoid connecting every domain row view directly to every other row view.

Report is slow:

- Use summary views for top-level pages.
- Use row views only for drill-through or detail pages.
- Confirm indexes from `sql/schema.sql` exist.
- Prefer Import mode for most SmartBI reports.
