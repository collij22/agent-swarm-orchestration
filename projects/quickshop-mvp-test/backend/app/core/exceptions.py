from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class QuickShopException(Exception):
    """Base exception for QuickShop application"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(QuickShopException):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class AuthorizationError(QuickShopException):
    """Authorization related errors"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)


class NotFoundError(QuickShopException):
    """Resource not found errors"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class ValidationError(QuickShopException):
    """Validation errors"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, 422)


class PaymentError(QuickShopException):
    """Payment processing errors"""
    def __init__(self, message: str = "Payment failed"):
        super().__init__(message, 402)


async def quickshop_exception_handler(request: Request, exc: QuickShopException):
    """Handle custom QuickShop exceptions"""
    logger.error(f"QuickShop exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "type": exc.__class__.__name__
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "HTTPException"
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database exceptions"""
    logger.error(f"Database exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Database error occurred",
            "type": "DatabaseError"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "type": "InternalServerError"
        }
    )


def setup_exception_handlers(app: FastAPI):
    """Setup all exception handlers"""
    app.add_exception_handler(QuickShopException, quickshop_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)