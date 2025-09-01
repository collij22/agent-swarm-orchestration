from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/quickshop"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    # Import all models to register them
    from models.user import User
    from models.product import Product, Category
    from models.cart import Cart, CartItem
    from models.order import Order, OrderItem
    
    Base.metadata.create_all(bind=engine)

def init_db():
    """Initialize database with tables and seed data"""
    create_tables()
    
    # Create sample data
    db = SessionLocal()
    try:
        # Import models
        from models.user import User
        from models.product import Product, Category
        from models.cart import Cart
        from models.order import Order
        
        # Check if data already exists
        if db.query(User).first() is not None:
            return
        
        # Create admin user
        admin_user = User(
            email="admin@quickshop.com",
            username="admin",
            hashed_password=User.get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            is_admin=True,
            address="123 Admin St, Admin City, AC 12345"
        )
        db.add(admin_user)
        
        # Create test user
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=User.get_password_hash("test123"),
            first_name="Test",
            last_name="User",
            address="456 Test Ave, Test City, TC 67890"
        )
        db.add(test_user)
        
        # Create categories
        electronics = Category(name="Electronics", description="Electronic devices and gadgets")
        clothing = Category(name="Clothing", description="Fashion and apparel")
        books = Category(name="Books", description="Books and literature")
        
        db.add_all([electronics, clothing, books])
        db.commit()
        
        # Create sample products
        products = [
            Product(
                name="iPhone 15 Pro",
                description="Latest iPhone with advanced features",
                price=999.99,
                sku="IPH15PRO001",
                stock_quantity=50,
                category_id=electronics.id,
                is_featured=True,
                image_url="https://via.placeholder.com/300x300?text=iPhone+15+Pro"
            ),
            Product(
                name="MacBook Air M2",
                description="Powerful laptop for professionals",
                price=1299.99,
                sku="MBA-M2-001",
                stock_quantity=25,
                category_id=electronics.id,
                is_featured=True,
                image_url="https://via.placeholder.com/300x300?text=MacBook+Air"
            ),
            Product(
                name="Premium T-Shirt",
                description="High quality cotton t-shirt",
                price=29.99,
                sku="TSH-PREM-001",
                stock_quantity=100,
                category_id=clothing.id,
                image_url="https://via.placeholder.com/300x300?text=T-Shirt"
            ),
            Product(
                name="Python Programming Book",
                description="Learn Python programming from scratch",
                price=49.99,
                sku="BOOK-PY-001",
                stock_quantity=75,
                category_id=books.id,
                image_url="https://via.placeholder.com/300x300?text=Python+Book"
            ),
        ]
        
        db.add_all(products)
        db.commit()
        
        print("Database initialized with sample data")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()