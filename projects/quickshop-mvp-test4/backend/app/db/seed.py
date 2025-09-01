"""
Seed database with sample data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.db.models import User, Category, Product
from app.core.security import get_password_hash
from app.core.config import settings

def seed_database():
    """Seed database with initial data"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if data already exists
        if db.query(User).first() or db.query(Product).first():
            print("🔄 Database already seeded, skipping...")
            db.close()
            return
        
        # Create admin user
        admin_user = User(
            email="admin@quickshop.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            is_admin=True,
            is_active=True
        )
        db.add(admin_user)
        
        # Create test user
        test_user = User(
            email="user@quickshop.com",
            username="testuser",
            hashed_password=get_password_hash("user123"),
            first_name="Test",
            last_name="User",
            is_admin=False,
            is_active=True
        )
        db.add(test_user)
        
        # Create categories
        categories = [
            Category(name="Electronics", description="Electronic devices and accessories"),
            Category(name="Clothing", description="Fashion and apparel"),
            Category(name="Books", description="Books and literature"),
            Category(name="Home & Garden", description="Home improvement and garden supplies"),
            Category(name="Sports", description="Sports and fitness equipment")
        ]
        
        for category in categories:
            db.add(category)
        
        db.commit()
        
        # Create products
        products = [
            # Electronics
            Product(
                name="Wireless Bluetooth Headphones",
                description="High-quality wireless headphones with noise cancellation",
                price=79.99,
                stock_quantity=50,
                category_id=1,
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500",
                is_active=True
            ),
            Product(
                name="Smartphone Case",
                description="Protective case for smartphones with wireless charging support",
                price=24.99,
                stock_quantity=100,
                category_id=1,
                image_url="https://images.unsplash.com/photo-1556656793-08538906a9f8?w=500",
                is_active=True
            ),
            Product(
                name="USB-C Charging Cable",
                description="Fast charging USB-C cable, 6ft length",
                price=12.99,
                stock_quantity=200,
                category_id=1,
                image_url="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500",
                is_active=True
            ),
            
            # Clothing
            Product(
                name="Cotton T-Shirt",
                description="Comfortable 100% cotton t-shirt, available in multiple colors",
                price=19.99,
                stock_quantity=75,
                category_id=2,
                image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500",
                is_active=True
            ),
            Product(
                name="Denim Jeans",
                description="Classic fit denim jeans, premium quality",
                price=49.99,
                stock_quantity=30,
                category_id=2,
                image_url="https://images.unsplash.com/photo-1542272604-787c3835535d?w=500",
                is_active=True
            ),
            
            # Books
            Product(
                name="Python Programming Guide",
                description="Complete guide to Python programming for beginners",
                price=29.99,
                stock_quantity=40,
                category_id=3,
                image_url="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500",
                is_active=True
            ),
            Product(
                name="Web Development Handbook",
                description="Modern web development techniques and best practices",
                price=34.99,
                stock_quantity=25,
                category_id=3,
                image_url="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500",
                is_active=True
            ),
            
            # Home & Garden
            Product(
                name="Indoor Plant Pot",
                description="Ceramic plant pot perfect for indoor plants",
                price=15.99,
                stock_quantity=60,
                category_id=4,
                image_url="https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=500",
                is_active=True
            ),
            Product(
                name="LED Desk Lamp",
                description="Adjustable LED desk lamp with USB charging port",
                price=39.99,
                stock_quantity=35,
                category_id=4,
                image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500",
                is_active=True
            ),
            
            # Sports
            Product(
                name="Yoga Mat",
                description="Non-slip yoga mat, eco-friendly material",
                price=24.99,
                stock_quantity=45,
                category_id=5,
                image_url="https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500",
                is_active=True
            )
        ]
        
        for product in products:
            db.add(product)
        
        db.commit()
        db.close()
        
        print("[DONE] Database seeded successfully!")
        print(f"Created {len(categories)} categories")
        print(f"Created {len(products)} products")
        print("Created admin user: admin@quickshop.com / admin123")
        print("Created test user: user@quickshop.com / user123")
        
    except Exception as e:
        print(f"❌ Seeding failed: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        sys.exit(1)

if __name__ == "__main__":
    seed_database()