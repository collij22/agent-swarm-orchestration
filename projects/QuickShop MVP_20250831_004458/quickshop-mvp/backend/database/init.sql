-- QuickShop MVP Database Initialization Script

-- Create database if it doesn't exist (handled by Docker)
-- CREATE DATABASE IF NOT EXISTS quickshop;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for performance
-- These will be created by SQLAlchemy, but we can add custom ones here

-- Index for product search
-- CREATE INDEX IF NOT EXISTS idx_products_name_search ON products USING gin(to_tsvector('english', name));
-- CREATE INDEX IF NOT EXISTS idx_products_description_search ON products USING gin(to_tsvector('english', description));

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active);
CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_cart_items_user_product ON cart_items(user_id, product_id);

-- Initial admin user will be created by the application
-- Sample data will be inserted by the application startup

COMMIT;