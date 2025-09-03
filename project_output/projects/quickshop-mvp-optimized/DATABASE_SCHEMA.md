# QuickShop MVP - Database Schema Specification

## Database Design Overview

### Database Type
- **Primary Database:** PostgreSQL 14+
- **Character Set:** UTF-8
- **Collation:** en_US.UTF-8

### Design Principles
- Normalized design (3NF) to reduce redundancy
- Foreign key constraints for data integrity
- Indexed columns for performance
- Audit trails with timestamps
- Soft deletes where applicable

## Core Tables

### 1. Users Table
```sql
Table: users
- id (UUID, PRIMARY KEY)
- email (VARCHAR(255), UNIQUE, NOT NULL)
- password_hash (VARCHAR(255), NOT NULL)
- first_name (VARCHAR(100), NOT NULL)
- last_name (VARCHAR(100), NOT NULL)
- phone (VARCHAR(20), NULLABLE)
- role (ENUM: 'customer', 'admin', DEFAULT 'customer')
- is_active (BOOLEAN, DEFAULT TRUE)
- email_verified (BOOLEAN, DEFAULT FALSE)
- created_at (TIMESTAMP, DEFAULT NOW())
- updated_at (TIMESTAMP, DEFAULT NOW())
- last_login (TIMESTAMP, NULLABLE)
```

**Indexes:**
- PRIMARY KEY on id
- UNIQUE INDEX on email
- INDEX on role
- INDEX on created_at

### 2. Categories Table
```sql
Table: categories
- id (UUID, PRIMARY KEY)
- name (VARCHAR(100), NOT NULL)
- slug (VARCHAR(100), UNIQUE, NOT NULL)
- description (TEXT, NULLABLE)
- parent_id (UUID, FOREIGN KEY REFERENCES categories(id), NULLABLE)
- image_url (VARCHAR(500), NULLABLE)
- is_active (BOOLEAN, DEFAULT TRUE)
- sort_order (INTEGER, DEFAULT 0)
- created_at (TIMESTAMP, DEFAULT NOW())
- updated_at (TIMESTAMP, DEFAULT NOW())
```

**Indexes:**
- PRIMARY KEY on id
- UNIQUE INDEX on slug
- INDEX on parent_id
- INDEX on is_active, sort_order

### 3. Products Table
```sql
Table: products
- id (UUID, PRIMARY KEY)
- name (VARCHAR(255), NOT NULL)
- slug (VARCHAR(255), UNIQUE, NOT NULL)
- description (TEXT, NULLABLE)
- short_description (VARCHAR(500), NULLABLE)
- price (DECIMAL(10,2), NOT NULL)
- compare_price (DECIMAL(10,2), NULLABLE)
- cost_price (DECIMAL(10,2), NULLABLE)
- sku (VARCHAR(100), UNIQUE, NULLABLE)
- barcode (VARCHAR(100), NULLABLE)
- track_inventory (BOOLEAN, DEFAULT TRUE)
- inventory_quantity (INTEGER, DEFAULT 0)
- allow_backorder (BOOLEAN, DEFAULT FALSE)
- weight (DECIMAL(8,2), NULLABLE)
- requires_shipping (BOOLEAN, DEFAULT TRUE)
- is_active (BOOLEAN, DEFAULT TRUE)
- is_featured (BOOLEAN, DEFAULT FALSE)
- meta_title (VARCHAR(255), NULLABLE)
- meta_description (VARCHAR(500), NULLABLE)
- created_at (TIMESTAMP, DEFAULT NOW())
- updated_at (TIMESTAMP, DEFAULT NOW())
```

**Indexes:**
- PRIMARY KEY on id
- UNIQUE INDEX on slug
- UNIQUE INDEX on sku
- INDEX on is_active
- INDEX on is_featured
- INDEX on price
- INDEX on created_at

### 4. Product Categories Junction Table
```sql
Table: product_categories
- product_id (UUID, FOREIGN KEY REFERENCES products(id), ON DELETE CASCADE)
- category_id (UUID, FOREIGN KEY REFERENCES categories(id), ON DELETE CASCADE)
- created_at (TIMESTAMP, DEFAULT NOW())
```

**Indexes:**
- PRIMARY KEY on (product_id, category_id)
- INDEX on category_id

### 5. Product Images Table
```sql
Table: product_images
- id (UUID, PRIMARY KEY)
- product_id (UUID, FOREIGN KEY REFERENCES products(id), ON DELETE CASCADE)
- image_url (VARCHAR(500), NOT NULL)
- alt_text (VARCHAR(255), NULLABLE)
- sort_order (INTEGER, DEFAULT 0)
- is_primary (BOOLEAN, DEFAULT FALSE)
- created_at (TIMESTAMP, DEFAULT NOW())
```

**Indexes:**
- PRIMARY KEY on id
- INDEX on product_id
- INDEX on sort_order

### 6. Shopping Cart Table
```sql
Table: shopping_carts
- id (UUID, PRIMARY KEY)
- user_id (UUID, FOREIGN KEY REFERENCES users(id), NULLABLE)
- session_id (VARCHAR(255), NULLABLE)
- created_at (TIMESTAMP, DEFAULT NOW())
- updated_at (TIMESTAMP, DEFAULT NOW())
```

**Indexes:**
- PRIMARY KEY on id
- INDEX on user_id
- INDEX on session_id

### 7. Cart Items Table
```sql
Table: cart_items
- id (UUID, PRIMARY KEY)
- cart_id (UUID, FOREIGN KEY REFERENCES shopping_carts(id), ON DELETE CASCADE)
- product_id (UUID, FOREIGN KEY REFERENCES products(id))
- quantity (INTEGER, NOT NULL, CHECK (quantity > 0))
- price (DECIMAL(10,2), NOT NULL)
- created_at (TIMESTAMP, DEFAULT NOW())
- updated_at (TIMESTAMP, DEFAULT NOW())
```

**Indexes:**
- PRIMARY KEY on id
- INDEX on cart_id
- INDEX on product_id

### 8. Orders Table
```sql
Table: orders
- id (UUID, PRIMARY KEY)
- order_number (VARCHAR(50), UNIQUE, NOT NULL)
- user_id (UUID, FOREIGN KEY REFERENCES users(id), NULLABLE)
- status (ENUM: 'pending', 'processing', 'shipped', 'delivered', 'cancelled', DEFAULT 'pending')
- subtotal (DECIMAL(10,2), NOT NULL)
- tax_amount (DECIMAL(10,2), DEFAULT 0)
- shipping_amount (DECIMAL(10,2), DEFAULT 0)
- total_amount (DECIMAL(10,2), NOT NULL)
- currency (VARCHAR(3), DEFAULT 'USD')
- payment_status (ENUM: 'pending', 'paid', 'failed', 'refunded', DEFAULT 'pending')
- payment_method (VARCHAR(50), NULLABLE)
- notes (TEXT, NULLABLE)
-
-- Billing Address
- billing_first_name (VARCHAR(100), NOT NULL)
- billing_last_name (VARCHAR(100), NOT NULL)
- billing_email (VARCHAR(255), NOT NULL)
- billing_phone (VARCHAR(20), NULLABLE)
- billing_address_line1 (VARCHAR(255), NOT NULL)
- billing_address_line2 (VARCHAR(255), NULLABLE)
- billing_city (VARCHAR(100), NOT NULL)
- billing_state (VARCHAR(100), NOT NULL)
- billing_postal_code (VARCHAR(20), NOT NULL)
- billing_country (VARCHAR(100), NOT NULL)

-- Shipping Address
- shipping_first_name (VARCHAR(100), NOT NULL)
- shipping_last_name (VARCHAR(100), NOT NULL)
- shipping_address_line1 (VARCHAR(255), NOT NULL)
- shipping_address_line2 (VARCHAR(255), NULLABLE)
- shipping_city (VARCHAR(100), NOT NULL)
- shipping_state (VARCHAR(100), NOT NULL)
- shipping_postal_code (VARCHAR(20), NOT NULL)
- shipping_country (VARCHAR(100), NOT NULL)

- created_at (TIMESTAMP, DEFAULT NOW())
- updated_at (TIMESTAMP, DEFAULT NOW())
- shipped_at (TIMESTAMP, NULLABLE)
- delivered_at (TIMESTAMP, NULLABLE)
```

**Indexes:**
- PRIMARY KEY on id
- UNIQUE INDEX on order_number
- INDEX on user_id
- INDEX on status
- INDEX on payment_status
- INDEX on created_at

### 9. Order Items Table
```sql
Table: order_items
- id (UUID, PRIMARY KEY)
- order_id (UUID, FOREIGN KEY REFERENCES orders(id), ON DELETE CASCADE)
- product_id (UUID, FOREIGN KEY REFERENCES products(id))
- product_name (VARCHAR(255), NOT NULL)
- product_sku (VARCHAR(100), NULLABLE)
- quantity (INTEGER, NOT NULL, CHECK (quantity > 0))
- unit_price (DECIMAL(10,2), NOT NULL)
- total_price (DECIMAL(10,2), NOT NULL)
- created_at (TIMESTAMP, DEFAULT NOW())
```

**Indexes:**
- PRIMARY KEY on id
- INDEX on order_id
- INDEX on product_id

### 10. User Sessions Table
```sql
Table: user_sessions
- id (UUID, PRIMARY KEY)
- user_id (UUID, FOREIGN KEY REFERENCES users(id), ON DELETE CASCADE)
- session_token (VARCHAR(255), UNIQUE, NOT NULL)
- refresh_token (VARCHAR(255), UNIQUE, NOT NULL)
- expires_at (TIMESTAMP, NOT NULL)
- created_at (TIMESTAMP, DEFAULT NOW())
- last_accessed (TIMESTAMP, DEFAULT NOW())
- ip_address (INET, NULLABLE)
- user_agent (TEXT, NULLABLE)
```

**Indexes:**
- PRIMARY KEY on id
- UNIQUE INDEX on session_token
- UNIQUE INDEX on refresh_token
- INDEX on user_id
- INDEX on expires_at

## Database Views

### 1. Product Catalog View
```sql
CREATE VIEW product_catalog AS
SELECT 
    p.id,
    p.name,
    p.slug,
    p.description,
    p.short_description,
    p.price,
    p.compare_price,
    p.sku,
    p.inventory_quantity,
    p.is_active,
    p.is_featured,
    p.created_at,
    p.updated_at,
    STRING_AGG(c.name, ', ') AS category_names,
    pi.image_url AS primary_image
FROM products p
LEFT JOIN product_categories pc ON p.id = pc.product_id
LEFT JOIN categories c ON pc.category_id = c.id
LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = true
WHERE p.is_active = true
GROUP BY p.id, pi.image_url;
```

### 2. Order Summary View
```sql
CREATE VIEW order_summary AS
SELECT 
    o.id,
    o.order_number,
    o.user_id,
    u.email AS customer_email,
    u.first_name || ' ' || u.last_name AS customer_name,
    o.status,
    o.total_amount,
    o.payment_status,
    o.created_at,
    COUNT(oi.id) AS item_count
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.email, u.first_name, u.last_name;
```

## Database Functions

### 1. Update Product Inventory
```sql
CREATE OR REPLACE FUNCTION update_product_inventory()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE products 
        SET inventory_quantity = inventory_quantity - NEW.quantity
        WHERE id = NEW.product_id;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE products 
        SET inventory_quantity = inventory_quantity + OLD.quantity - NEW.quantity
        WHERE id = NEW.product_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE products 
        SET inventory_quantity = inventory_quantity + OLD.quantity
        WHERE id = OLD.product_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

### 2. Generate Order Number
```sql
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.order_number := 'ORD-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || 
                       LPAD(NEXTVAL('order_sequence')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## Database Triggers

### 1. Order Items Inventory Trigger
```sql
CREATE TRIGGER order_items_inventory_trigger
    AFTER INSERT OR UPDATE OR DELETE ON order_items
    FOR EACH ROW EXECUTE FUNCTION update_product_inventory();
```

### 2. Order Number Generation Trigger
```sql
CREATE SEQUENCE order_sequence START 1;

CREATE TRIGGER generate_order_number_trigger
    BEFORE INSERT ON orders
    FOR EACH ROW EXECUTE FUNCTION generate_order_number();
```

### 3. Updated At Triggers
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at column
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shopping_carts_updated_at BEFORE UPDATE ON shopping_carts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Data Integrity Constraints

### Business Rules
1. **Product Pricing:** Price must be greater than 0
2. **Inventory:** Quantity cannot be negative unless backorders allowed
3. **Order Total:** Must match sum of line items plus tax and shipping
4. **Cart Items:** Quantity must be positive
5. **User Email:** Must be unique and valid format

### Referential Integrity
- All foreign keys have appropriate ON DELETE actions
- Cascade deletes for dependent data (cart items, order items)
- Restrict deletes for referenced data (products in orders)

## Performance Considerations

### Indexing Strategy
- Primary keys for all tables
- Foreign key indexes for join performance
- Composite indexes for common query patterns
- Partial indexes for filtered queries

### Query Optimization
- Use views for complex joins
- Implement pagination for large result sets
- Cache frequently accessed data
- Use connection pooling

### Partitioning (Future)
- Consider partitioning orders table by date
- Partition user sessions by expiry date
- Archive old data to separate tables

## Security Considerations

### Data Protection
- Password hashing with bcrypt
- Sensitive data encryption at rest
- PII data handling compliance
- Audit logging for sensitive operations

### Access Control
- Database user roles and permissions
- Application-level access control
- Row-level security where needed
- Connection encryption (SSL/TLS)

## Backup and Recovery

### Backup Strategy
- Daily full backups
- Transaction log backups every 15 minutes
- Point-in-time recovery capability
- Cross-region backup replication

### Recovery Procedures
- Automated backup verification
- Recovery time objective (RTO): 1 hour
- Recovery point objective (RPO): 15 minutes
- Disaster recovery testing schedule