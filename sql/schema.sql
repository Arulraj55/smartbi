create table if not exists smartbi_uploads (
    id bigserial primary key,
    file_name text not null,
    domain_name text not null,
    confidence numeric(5, 2) not null default 0,
    row_count integer not null default 0,
    summary_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists smartbi_clean_rows (
    id bigserial primary key,
    upload_id bigint not null references smartbi_uploads(id) on delete cascade,
    row_number integer not null,
    row_data jsonb not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_smartbi_uploads_created_at on smartbi_uploads (created_at desc);
create index if not exists idx_smartbi_clean_rows_upload_id on smartbi_clean_rows (upload_id);
create index if not exists idx_smartbi_uploads_domain_created_at on smartbi_uploads (domain_name, created_at desc);
create index if not exists idx_smartbi_clean_rows_upload_row_number on smartbi_clean_rows (upload_id, row_number);
create index if not exists idx_smartbi_clean_rows_row_data_gin on smartbi_clean_rows using gin (row_data);
create index if not exists idx_smartbi_clean_rows_company on smartbi_clean_rows ((lower(coalesce(row_data->>'Company', row_data->>'company', row_data->>'Company Name', ''))));
create index if not exists idx_smartbi_clean_rows_department on smartbi_clean_rows ((lower(coalesce(row_data->>'Department', row_data->>'department', row_data->>'Dept', row_data->>'Branch', ''))));
create index if not exists idx_smartbi_clean_rows_region on smartbi_clean_rows ((lower(coalesce(row_data->>'Region', row_data->>'region', row_data->>'State', row_data->>'City', ''))));
