-- SmartBI Power BI reporting views.
-- Run after sql/schema.sql. These views keep the application schema unchanged
-- while exposing typed, Power BI-friendly reporting shapes.

create or replace view v_smartbi_upload_summary as
select
    id as upload_id,
    id,
    file_name,
    domain_name,
    confidence,
    row_count,
    summary_json,
    created_at,
    created_at::date as upload_date,
    date_trunc('month', created_at)::date as upload_month,
    extract(year from created_at)::integer as upload_year
from smartbi_uploads;

create or replace view v_smartbi_kpis as
select
    domain_name,
    count(*) as upload_count,
    sum(row_count) as total_rows,
    round(avg(confidence)::numeric, 2) as average_confidence,
    max(created_at) as last_upload_at
from smartbi_uploads
group by domain_name;

create or replace view v_smartbi_rows_flat as
select
    r.id as clean_row_id,
    r.upload_id,
    r.row_number,
    r.row_data,
    r.created_at as row_created_at,
    u.file_name,
    u.domain_name,
    u.confidence,
    u.created_at as upload_created_at,
    u.created_at::date as upload_date,
    date_trunc('month', u.created_at)::date as upload_month,
    extract(year from u.created_at)::integer as upload_year
from smartbi_clean_rows r
join smartbi_uploads u on u.id = r.upload_id;

create or replace view v_smartbi_latest_rows as
select
    clean_row_id as id,
    upload_id,
    row_number,
    row_data,
    domain_name,
    file_name,
    upload_created_at
from v_smartbi_rows_flat;

create or replace view v_smartbi_domain_upload_monthly as
select
    domain_name,
    upload_month as month,
    count(distinct upload_id) as uploads,
    count(*) as clean_rows,
    round(avg(confidence)::numeric, 2) as average_confidence
from v_smartbi_rows_flat
group by domain_name, upload_month;

create or replace view v_smartbi_placement_rows as
select
    clean_row_id,
    upload_id,
    row_number,
    file_name,
    upload_date,
    upload_month,
    upload_year,
    coalesce(row_data->>'Candidate Name', row_data->>'candidate_name', row_data->>'Student Name', row_data->>'student_name') as student_name,
    coalesce(row_data->>'Company', row_data->>'company', row_data->>'Company Name', row_data->>'company_name', row_data->>'Employer') as company,
    coalesce(row_data->>'Department', row_data->>'department', row_data->>'Branch', row_data->>'branch', row_data->>'Course') as department,
    coalesce(row_data->>'Gender', row_data->>'gender', row_data->>'Sex') as gender,
    coalesce(row_data->>'Status', row_data->>'status', row_data->>'Placement Status', row_data->>'Result') as placement_status,
    case
        when coalesce(row_data->>'Offer CTC', row_data->>'offer_ctc', row_data->>'Package', row_data->>'package', row_data->>'CTC') ~ '^-?[0-9]+(\.[0-9]+)?$'
        then coalesce(row_data->>'Offer CTC', row_data->>'offer_ctc', row_data->>'Package', row_data->>'package', row_data->>'CTC')::numeric
        else null
    end as package_amount,
    case
        when lower(coalesce(row_data->>'Status', row_data->>'status', row_data->>'Placement Status', row_data->>'Result', '')) in ('placed', 'selected', 'hired', 'joined', 'offer accepted', 'converted')
             or coalesce(row_data->>'Offer CTC', row_data->>'offer_ctc', row_data->>'Package', row_data->>'package', row_data->>'CTC') is not null
        then 1 else 0
    end as placed_flag,
    row_data
from v_smartbi_rows_flat
where domain_name = 'Placement Management';

create or replace view v_smartbi_placement_summary as
select
    upload_id,
    file_name,
    count(*) as total_students,
    sum(placed_flag) as placed_students,
    round((sum(placed_flag)::numeric / nullif(count(*), 0)) * 100, 2) as placement_percentage,
    round(avg(package_amount), 2) as average_package,
    max(package_amount) as highest_package,
    min(package_amount) as lowest_package
from v_smartbi_placement_rows
group by upload_id, file_name;

create or replace view v_smartbi_placement_company_summary as
select upload_id, company, count(*) as students, sum(placed_flag) as placed_students, round(avg(package_amount), 2) as average_package
from v_smartbi_placement_rows
where company is not null
group by upload_id, company;

create or replace view v_smartbi_placement_department_summary as
select upload_id, department, count(*) as students, sum(placed_flag) as placed_students, round(avg(package_amount), 2) as average_package
from v_smartbi_placement_rows
where department is not null
group by upload_id, department;

create or replace view v_smartbi_hr_rows as
select
    clean_row_id,
    upload_id,
    row_number,
    file_name,
    upload_date,
    upload_month,
    upload_year,
    coalesce(row_data->>'Employee Name', row_data->>'employee_name', row_data->>'Employee', row_data->>'employee') as employee_name,
    coalesce(row_data->>'Department', row_data->>'department', row_data->>'Dept', row_data->>'Team') as department,
    coalesce(row_data->>'Gender', row_data->>'gender', row_data->>'Sex') as gender,
    case
        when coalesce(row_data->>'Salary', row_data->>'salary', row_data->>'Annual Salary', row_data->>'Compensation') ~ '^-?[0-9]+(\.[0-9]+)?$'
        then coalesce(row_data->>'Salary', row_data->>'salary', row_data->>'Annual Salary', row_data->>'Compensation')::numeric
        else null
    end as salary,
    case
        when coalesce(row_data->>'Experience', row_data->>'experience', row_data->>'Years Experience', row_data->>'Service Years') ~ '^-?[0-9]+(\.[0-9]+)?$'
        then coalesce(row_data->>'Experience', row_data->>'experience', row_data->>'Years Experience', row_data->>'Service Years')::numeric
        else null
    end as experience_years,
    lower(coalesce(row_data->>'Attendance Status', row_data->>'attendance_status', row_data->>'Attendance', row_data->>'Status', '')) as attendance_status,
    lower(coalesce(row_data->>'Attrition', row_data->>'attrition', row_data->>'Resigned', row_data->>'Left', row_data->>'Exit Status', '')) as attrition_status,
    row_data
from v_smartbi_rows_flat
where domain_name = 'HR Management';

create or replace view v_smartbi_hr_summary as
select
    upload_id,
    file_name,
    count(*) as employees,
    count(distinct department) as departments,
    round(avg(salary), 2) as average_salary,
    round(avg(experience_years), 2) as average_experience,
    sum(case when attendance_status in ('present', 'active', '1', 'yes') then 1 else 0 end) as attendance_hits,
    round((sum(case when attendance_status in ('present', 'active', '1', 'yes') then 1 else 0 end)::numeric / nullif(count(*), 0)) * 100, 2) as attendance_percentage,
    sum(case when attrition_status in ('yes', 'true', 'left', 'resigned', 'terminated') then 1 else 0 end) as attrition_count
from v_smartbi_hr_rows
group by upload_id, file_name;

create or replace view v_smartbi_sales_rows as
select
    clean_row_id,
    upload_id,
    row_number,
    file_name,
    upload_date,
    upload_month,
    upload_year,
    coalesce(row_data->>'Order ID', row_data->>'order_id', row_data->>'Invoice ID', row_data->>'invoice_id') as order_id,
    coalesce(row_data->>'Customer', row_data->>'customer', row_data->>'Customer Name', row_data->>'Client', row_data->>'Buyer') as customer,
    coalesce(row_data->>'Product', row_data->>'product', row_data->>'Product Name', row_data->>'Item', row_data->>'SKU') as product,
    coalesce(row_data->>'Category', row_data->>'category', row_data->>'Product Category', row_data->>'Segment') as category,
    coalesce(row_data->>'Region', row_data->>'region', row_data->>'Territory', row_data->>'Zone', row_data->>'State', row_data->>'City') as region,
    case
        when coalesce(row_data->>'Revenue Amount', row_data->>'Amount', row_data->>'amount', row_data->>'Revenue', row_data->>'Sales', row_data->>'Total', row_data->>'Value') ~ '^-?[0-9]+(\.[0-9]+)?$'
        then coalesce(row_data->>'Revenue Amount', row_data->>'Amount', row_data->>'amount', row_data->>'Revenue', row_data->>'Sales', row_data->>'Total', row_data->>'Value')::numeric
        else null
    end as revenue_amount,
    row_data
from v_smartbi_rows_flat
where domain_name = 'Retail Sales';

create or replace view v_smartbi_sales_summary as
select
    upload_id,
    file_name,
    coalesce(sum(revenue_amount), 0) as revenue,
    count(*) as orders,
    round(coalesce(sum(revenue_amount), 0) / nullif(count(*), 0), 2) as average_order_value,
    count(distinct customer) as customers,
    count(distinct product) as products,
    count(distinct region) as regions
from v_smartbi_sales_rows
group by upload_id, file_name;

create or replace view v_smartbi_sales_monthly_revenue as
select upload_id, upload_month as month, coalesce(sum(revenue_amount), 0) as revenue, count(*) as orders
from v_smartbi_sales_rows
group by upload_id, upload_month;

create or replace view v_smartbi_sales_region_summary as
select upload_id, region, coalesce(sum(revenue_amount), 0) as revenue, count(*) as orders
from v_smartbi_sales_rows
where region is not null
group by upload_id, region;

create or replace view v_smartbi_inventory_rows as
select
    clean_row_id,
    upload_id,
    row_number,
    file_name,
    upload_date,
    upload_month,
    upload_year,
    coalesce(row_data->>'Product', row_data->>'product', row_data->>'Product Name', row_data->>'Item', row_data->>'SKU') as product,
    coalesce(row_data->>'Category', row_data->>'category', row_data->>'Product Category', row_data->>'Type') as category,
    coalesce(row_data->>'Supplier', row_data->>'supplier', row_data->>'Vendor', row_data->>'Provider') as supplier,
    case when coalesce(row_data->>'Stock Qty', row_data->>'stock_qty', row_data->>'Quantity', row_data->>'Qty', row_data->>'Stock', row_data->>'On Hand') ~ '^-?[0-9]+(\.[0-9]+)?$'
        then coalesce(row_data->>'Stock Qty', row_data->>'stock_qty', row_data->>'Quantity', row_data->>'Qty', row_data->>'Stock', row_data->>'On Hand')::numeric else 0 end as stock_quantity,
    case when coalesce(row_data->>'Reorder Level', row_data->>'reorder_level', row_data->>'Reorder', row_data->>'Minimum Stock', row_data->>'Min Stock') ~ '^-?[0-9]+(\.[0-9]+)?$'
        then coalesce(row_data->>'Reorder Level', row_data->>'reorder_level', row_data->>'Reorder', row_data->>'Minimum Stock', row_data->>'Min Stock')::numeric else 0 end as reorder_level,
    case when coalesce(row_data->>'Unit Price', row_data->>'unit_price', row_data->>'Price', row_data->>'Cost', row_data->>'Rate') ~ '^-?[0-9]+(\.[0-9]+)?$'
        then coalesce(row_data->>'Unit Price', row_data->>'unit_price', row_data->>'Price', row_data->>'Cost', row_data->>'Rate')::numeric else 0 end as unit_price,
    row_data
from v_smartbi_rows_flat
where domain_name = 'Inventory';

create or replace view v_smartbi_inventory_summary as
select
    upload_id,
    file_name,
    count(*) as products,
    sum(case when stock_quantity <= reorder_level then 1 else 0 end) as low_stock,
    sum(case when stock_quantity <= 0 then 1 else 0 end) as out_of_stock,
    coalesce(sum(stock_quantity * unit_price), 0) as stock_value,
    count(distinct supplier) as suppliers
from v_smartbi_inventory_rows
group by upload_id, file_name;

create or replace view v_smartbi_attendance_rows as
select
    clean_row_id,
    upload_id,
    row_number,
    file_name,
    upload_date,
    upload_month,
    upload_year,
    coalesce(row_data->>'Student Name', row_data->>'student_name', row_data->>'Student', row_data->>'Name') as student_name,
    coalesce(row_data->>'Class', row_data->>'class', row_data->>'Section', row_data->>'Batch', row_data->>'Grade') as class_name,
    coalesce(row_data->>'Subject', row_data->>'subject', row_data->>'Course', row_data->>'Paper') as subject,
    lower(coalesce(row_data->>'Attendance', row_data->>'attendance', row_data->>'Status', row_data->>'Presence', row_data->>'Present Absent', '')) as attendance_status,
    row_data
from v_smartbi_rows_flat
where domain_name = 'Student Attendance';

create or replace view v_smartbi_attendance_summary as
select
    upload_id,
    file_name,
    count(*) as attendance_rows,
    sum(case when attendance_status in ('present', 'p', 'yes', '1', 'available') then 1 else 0 end) as present_count,
    sum(case when attendance_status in ('absent', 'a', 'no', '0', 'leave') then 1 else 0 end) as absent_count,
    round((sum(case when attendance_status in ('present', 'p', 'yes', '1', 'available') then 1 else 0 end)::numeric / nullif(count(*), 0)) * 100, 2) as attendance_percentage,
    count(distinct class_name) as classes,
    count(distinct subject) as subjects
from v_smartbi_attendance_rows
group by upload_id, file_name;

create or replace view v_smartbi_generic_rows as
select
    f.clean_row_id,
    f.upload_id,
    f.row_number,
    f.file_name,
    f.upload_date,
    f.upload_month,
    f.upload_year,
    e.key as column_name,
    e.value as column_value,
    case when e.value is null or btrim(e.value) = '' then 1 else 0 end as missing_flag,
    f.row_data
from v_smartbi_rows_flat f
cross join lateral jsonb_each_text(f.row_data) as e(key, value)
where f.domain_name = 'Generic';

create or replace view v_smartbi_generic_summary as
select
    upload_id,
    file_name,
    count(distinct clean_row_id) as rows,
    count(distinct column_name) as columns,
    sum(missing_flag) as missing_values
from v_smartbi_generic_rows
group by upload_id, file_name;

-- Backward-compatible monthly views for existing Power BI prototypes.
create or replace view v_smartbi_placement_monthly as
select month, uploads, clean_rows as total_rows, average_confidence
from v_smartbi_domain_upload_monthly
where domain_name = 'Placement Management';

create or replace view v_smartbi_hr_monthly as
select month, uploads, clean_rows as total_rows, average_confidence
from v_smartbi_domain_upload_monthly
where domain_name = 'HR Management';

create or replace view v_smartbi_sales_monthly as
select month, uploads, clean_rows as total_rows, average_confidence
from v_smartbi_domain_upload_monthly
where domain_name = 'Retail Sales';

create or replace view v_smartbi_inventory_monthly as
select month, uploads, clean_rows as total_rows, average_confidence
from v_smartbi_domain_upload_monthly
where domain_name = 'Inventory';

create or replace view v_smartbi_attendance_monthly as
select month, uploads, clean_rows as total_rows, average_confidence
from v_smartbi_domain_upload_monthly
where domain_name = 'Student Attendance';

create or replace view v_smartbi_generic_monthly as
select month, uploads, clean_rows as total_rows, average_confidence
from v_smartbi_domain_upload_monthly
where domain_name = 'Generic';
