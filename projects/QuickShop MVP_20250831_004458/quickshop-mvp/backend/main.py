from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import os
from datetime import datetime, timedelta
import jwt
from typing import Optional

from database.connection import init_db, get_db
from routers import auth, products, cart, orders, admin, payments
from models.database import User, Product, Order
from utils.auth import get_current_user
from utils.sample_data import create_sample_data

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key")
JWT_ALGORITHM = "HS256"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await create_sample_data()
    print("🚀 QuickShop MVP started successfully!")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🛍️ Frontend: http://localhost:3000")
    yield
    # Shutdown
    print("👋 QuickShop MVP shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="QuickShop MVP API",
    description="Modern e-commerce platform with essential features",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(cart.router, prefix="/api/cart", tags=["Shopping Cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
async def root():
    """Welcome endpoint with API information."""
    return {
        "message": "Welcome to QuickShop MVP API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
        "features": [
            "User Authentication",
            "Product Catalog",
            "Shopping Cart",
            "Order Management",
            "Payment Processing",
            "Admin Dashboard"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    """Get platform statistics (requires authentication)."""
    db = next(get_db())
    
    try:
        total_products = db.query(Product).count()
        total_orders = db.query(Order).count()
        total_users = db.query(User).count()
        
        return {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_users": total_users,
            "platform_status": "operational"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )