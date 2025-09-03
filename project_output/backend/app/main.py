from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .models import Base
from .routers import auth, products, cart, orders

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QuickShop API",
    description="A simple e-commerce API built with FastAPI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to QuickShop API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}