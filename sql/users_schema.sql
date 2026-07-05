-- Add users table for multi-user authentication
create table if not exists smartbi_users (
    id bigserial primary key,
    username text not null unique,
    email text not null unique,
    password_hash text not null,
    full_name text,
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);

-- Add user_id to uploads table
alter table smartbi_uploads add column if not exists user_id bigint references smartbi_users(id);

-- Create index
create index if not exists idx_smartbi_users_username on smartbi_users (username);
create index if not exists idx_smartbi_users_email on smartbi_users (email);
create index if not exists idx_smartbi_uploads_user_id on smartbi_uploads (user_id);
