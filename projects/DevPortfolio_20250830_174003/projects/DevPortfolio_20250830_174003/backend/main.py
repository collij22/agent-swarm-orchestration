"""
DevPortfolio - Professional Developer Portfolio & Blog Platform
Main FastAPI Application with AI-powered content assistance
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from datetime import datetime
import logging

# Import routers
from routers import portfolio, blog, auth, analytics, contact
from database.connection import get_database
from services.ai_service import AIService
from services.github_service import GitHubService
from services.analytics_service import AnalyticsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DevPortfolio API",
    description="Professional developer portfolio and blog platform with AI-powered content assistance",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security
security = HTTPBearer()

# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.herokuapp.com"]
)

# Static files for uploaded content
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error occurred"
    )

# Health check endpoint
@app.get("/api/health")
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
    """API root endpoint"""
    return {
        "message": "DevPortfolio API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting DevPortfolio API...")
    
    # Initialize database
    try:
        db = await get_database()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    # Initialize external services
    try:
        ai_service = AIService()
        github_service = GitHubService()
        analytics_service = AnalyticsService()
        logger.info("External services initialized")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down DevPortfolio API...")

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )