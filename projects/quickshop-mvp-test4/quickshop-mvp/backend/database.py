from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://quickshop:password@localhost:5432/quickshop_db")

# Create engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    """Create all tables and seed initial data"""
    from models import User, Product, Category, Order, OrderItem, Cart, CartItem
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Seed initial data
    db = SessionLocal()
    try:
        # Check if categories exist
        if not db.query(Category).first():
            # Create categories
            categories = [
                Category(name="Electronics", description="Electronic devices and gadgets"),
                Category(name="Clothing", description="Fashion and apparel"),
                Category(name="Books", description="Books and literature"),
                Category(name="Home & Garden", description="Home improvement and gardening"),
                Category(name="Sports", description="Sports and outdoor activities")
            ]
            db.add_all(categories)
            db.commit()
            
            # Create sample products
            products = [
                Product(
                    name="Wireless Bluetooth Headphones",
                    description="High-quality wireless headphones with noise cancellation",
                    price=99.99,
                    stock_quantity=50,
                    category_id=1,
                    image_url="https://via.placeholder.com/300x300?text=Headphones"
                ),
                Product(
                    name="Premium Cotton T-Shirt",
                    description="Comfortable and stylish cotton t-shirt",
                    price=29.99,
                    stock_quantity=100,
                    category_id=2,
                    image_url="https://via.placeholder.com/300x300?text=T-Shirt"
                ),
                Product(
                    name="Programming Book Collection",
                    description="Complete guide to modern programming languages",
                    price=49.99,
                    stock_quantity=25,
                    category_id=3,
                    image_url="https://via.placeholder.com/300x300?text=Books"
                ),
                Product(
                    name="Smart Home Security Camera",
                    description="WiFi enabled security camera with mobile app",
                    price=149.99,
                    stock_quantity=30,
                    category_id=1,
                    image_url="https://via.placeholder.com/300x300?text=Camera"
                ),
                Product(
                    name="Yoga Mat Premium",
                    description="Non-slip yoga mat for all fitness levels",
                    price=39.99,
                    stock_quantity=75,
                    category_id=5,
                    image_url="https://via.placeholder.com/300x300?text=Yoga+Mat"
                )
            ]
            db.add_all(products)
            db.commit()
            
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()