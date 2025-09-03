-- quickshop_schema.sql - Database schema for QuickShop MVP

-- Create database
CREATE DATABASE IF NOT EXISTS quickshop_mvp;
USE quickshop_mvp;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(50) DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    category VARCHAR(100),
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_price (price),
    INDEX idx_created_at (created_at)
);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address JSON,
    payment_method VARCHAR(50),
    payment_id VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Order items table
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
);

-- Insert sample data
INSERT INTO users (email, password_hash, first_name, last_name, role) VALUES
('admin@example.com', '$2b$10$YourHashHere', 'Admin', 'User', 'admin'),
('test@example.com', '$2b$10$YourHashHere', 'Test', 'User', 'customer'),
('john@example.com', '$2b$10$YourHashHere', 'John', 'Doe', 'customer');

INSERT INTO products (name, description, price, stock, category) VALUES
('Laptop', 'High-performance laptop with 16GB RAM', 999.99, 10, 'Electronics'),
('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 50, 'Electronics'),
('Office Chair', 'Comfortable ergonomic office chair', 299.99, 15, 'Furniture'),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 49.99, 30, 'Furniture'),
('Notebook', 'Premium quality notebook', 9.99, 100, 'Stationery');

-- Create views
CREATE VIEW active_products AS
SELECT * FROM products WHERE is_active = TRUE;

CREATE VIEW order_summary AS
SELECT 
    o.id,
    o.user_id,
    u.email,
    o.total,
    o.status,
    o.created_at,
    COUNT(oi.id) as item_count
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.user_id, u.email, o.total, o.status, o.created_at;
