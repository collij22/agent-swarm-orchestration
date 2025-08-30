"""
DevPortfolio FastAPI Backend
Professional developer portfolio and blog platform with AI-powered content assistance
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
from datetime import datetime

# Import routers
from routers import (
    portfolio_router,
    blog_router,
    auth_router,
    analytics_router,
    contact_router,
    ai_assistant_router
)
from database import init_db
from middleware.rate_limiting import RateLimitMiddleware
from middleware.security import SecurityMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting DevPortfolio API...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down DevPortfolio API...")

# Create FastAPI application
app = FastAPI(
    title="DevPortfolio API",
    description="Professional developer portfolio and blog platform with AI-powered content assistance",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Security middleware
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "your-domain.com"]
)

# Custom middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(blog_router, prefix="/api/blog", tags=["Blog"])
app.include_router(ai_assistant_router, prefix="/api/ai", tags=["AI Assistant"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(contact_router, prefix="/api/contact", tags=["Contact"])

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API status"""
    return {
        "message": "DevPortfolio API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/api/docs"
    }

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )