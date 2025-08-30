from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.core.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_password_hash,
    get_user_by_email,
    get_user_by_username
)
from src.core.config import settings
from src.models.models import User
from src.schemas.schemas import (
    UserCreate, UserResponse, UserUpdate,
    Token, LoginRequest
)

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if username already exists
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        bio=user_data.bio,
        location=user_data.location,
        website=str(user_data.website) if user_data.website else None,
        github_username=user_data.github_username,
        linkedin_url=str(user_data.linkedin_url) if user_data.linkedin_url else None,
        hashed_password=hashed_password,
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token"""
    user = await authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        if field in ["website", "linkedin_url"] and value:
            value = str(value)
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    from src.core.auth import verify_password
    
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    await db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    """Logout user (client should discard the token)"""
    return {"message": "Successfully logged out"}

# OAuth routes (simplified for demo - would need proper OAuth implementation)
@router.get("/oauth/github")
async def github_oauth_login():
    """Initiate GitHub OAuth login"""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&scope=user:email"
        f"&state=random_state_string"
    )
    return {"auth_url": github_auth_url}

@router.post("/oauth/github/callback")
async def github_oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle GitHub OAuth callback"""
    # This is a simplified version - in production, you'd:
    # 1. Exchange code for access token
    # 2. Get user info from GitHub API
    # 3. Create or update user in database
    # 4. Return JWT token
    
    # For demo purposes, return a placeholder response
    return {"message": "OAuth callback received", "code": code}

@router.get("/oauth/google")
async def google_oauth_login():
    """Initiate Google OAuth login"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&redirect_uri=http://localhost:8000/api/v1/auth/oauth/google/callback"
        f"&state=random_state_string"
    )
    return {"auth_url": google_auth_url}

@router.post("/oauth/google/callback")
async def google_oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google OAuth callback"""
    # This is a simplified version - in production, you'd:
    # 1. Exchange code for access token
    # 2. Get user info from Google API
    # 3. Create or update user in database
    # 4. Return JWT token
    
    # For demo purposes, return a placeholder response
    return {"message": "OAuth callback received", "code": code}