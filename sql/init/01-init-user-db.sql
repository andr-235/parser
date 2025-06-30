-- Initialize VK Monitor Database and User
-- This script runs when PostgreSQL container starts for the first time

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE vk_monitor_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vk_monitor_dev')\gexec

-- Create user if it doesn't exist and grant permissions
DO $$
BEGIN
    -- Create user if not exists
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'vk_monitor') THEN
        CREATE USER vk_monitor WITH PASSWORD 'privet123';
    END IF;
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE vk_monitor_dev TO vk_monitor;
    
    -- Make user owner of the database
    ALTER DATABASE vk_monitor_dev OWNER TO vk_monitor;
END
$$;

-- Connect to the vk_monitor_dev database and grant schema permissions
\c vk_monitor_dev;

-- Grant all privileges on public schema
GRANT ALL ON SCHEMA public TO vk_monitor;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO vk_monitor;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO vk_monitor;

-- Grant privileges on future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO vk_monitor;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO vk_monitor; 