"""
Database migrations for QuickShop
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.db.database import Base
from app.db.models import User, Category, Product, CartItem, Order
from app.core.config import settings

def run_migrations():
    """Create all database tables"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("[DONE] Database migrations completed successfully!")
        print("Created tables:")
        for table in Base.metadata.tables.keys():
            print(f"  - {table}")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()