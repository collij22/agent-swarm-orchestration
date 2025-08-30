"""
DevPortfolio - Professional Developer Portfolio and Blog Platform
Main FastAPI application entry point
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime

# Import routers
from routers import portfolio, blog, auth, analytics, contact
from database import init_db, get_db
from models.base import Base
from utils.security import verify_api_key
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting DevPortfolio application...")
    
    # Initialize database
    await init_db()
    
    yield
    
    logger.info("Shutting down DevPortfolio application...")

# Create FastAPI app
app = FastAPI(
    title="DevPortfolio API",
    description="Professional Developer Portfolio and Blog Platform with AI-powered content assistance",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure properly for production
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Add production URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "DevPortfolio API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

# Include routers
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(blog.router, prefix="/api/v1/blog", tags=["Blog"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(contact.router, prefix="/api/v1/contact", tags=["Contact"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )