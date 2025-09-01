from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Product
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).first() or db.query(Product).first():
            print("Database already seeded")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@quickshop.com",
            username="admin",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(admin_user)
        
        # Create regular user
        regular_user = User(
            email="user@quickshop.com",
            username="testuser",
            full_name="Test User",
            hashed_password=get_password_hash("user123"),
            is_admin=False
        )
        db.add(regular_user)
        
        # Create sample products
        products = [
            Product(
                name="Wireless Bluetooth Headphones",
                description="High-quality wireless headphones with noise cancellation",
                price=99.99,
                category="Electronics",
                stock_quantity=50,
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"
            ),
            Product(
                name="Smartphone Case",
                description="Protective case for your smartphone with premium materials",
                price=29.99,
                category="Accessories",
                stock_quantity=100,
                image_url="https://images.unsplash.com/photo-1601593346740-925612772716?w=500"
            ),
            Product(
                name="Laptop Stand",
                description="Adjustable laptop stand for better ergonomics",
                price=49.99,
                category="Office",
                stock_quantity=75,
                image_url="https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500"
            ),
            Product(
                name="Coffee Mug",
                description="Ceramic coffee mug with modern design",
                price=19.99,
                category="Home",
                stock_quantity=200,
                image_url="https://images.unsplash.com/photo-1514228742587-6b1558fcf93a?w=500"
            ),
            Product(
                name="Fitness Tracker",
                description="Smart fitness tracker with heart rate monitoring",
                price=79.99,
                category="Health",
                stock_quantity=30,
                image_url="https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=500"
            ),
            Product(
                name="Backpack",
                description="Durable backpack for everyday use",
                price=59.99,
                category="Fashion",
                stock_quantity=40,
                image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500"
            )
        ]
        
        for product in products:
            db.add(product)
        
        db.commit()
        print("Database seeded successfully!")
        print("Admin user: admin@quickshop.com / admin123")
        print("Test user: user@quickshop.com / user123")
        print(f"Created {len(products)} products")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()