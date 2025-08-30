"""
Blog router for markdown-based blog engine
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.blog import Post, Category, Tag, Comment, PostStatus, CommentStatus
from models.user import User
from utils.security import verify_api_key, get_current_user
from utils.markdown import render_markdown, calculate_reading_time
from utils.ai import get_ai_suggestions, analyze_seo
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Pydantic schemas
from pydantic import BaseModel, Field
from typing import Dict, Any


class PostResponse(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    html_content: Optional[str]
    featured_image: Optional[str]
    status: str
    published_at: Optional[datetime]
    meta_title: Optional[str]
    meta_description: Optional[str]
    is_featured: bool
    view_count: int
    like_count: int
    comment_count: int
    reading_time: Optional[int]
    category: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    featured_image: Optional[str]
    published_at: Optional[datetime]
    is_featured: bool
    view_count: int
    comment_count: int
    reading_time: Optional[int]
    category: Optional[str] = None
    tags: List[str] = []

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    post_count: int

    class Config:
        from_attributes = True


class TagResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    color: Optional[str]
    post_count: int

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: str
    author_name: str
    author_website: Optional[str]
    content: str
    html_content: Optional[str]
    status: str
    created_at: datetime
    children: List['CommentResponse'] = []

    class Config:
        from_attributes = True


class CreateCommentRequest(BaseModel):
    author_name: str = Field(..., min_length=1, max_length=100)
    author_email: str = Field(..., min_length=1, max_length=255)
    author_website: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1)
    parent_id: Optional[str] = None


# Public endpoints
@router.get("/posts", response_model=List[PostListResponse])
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get published blog posts with optional filtering"""
    try:
        query = select(Post).where(
            Post.status == PostStatus.PUBLISHED,
            Post.published_at <= datetime.utcnow()
        )
        
        if featured_only:
            query = query.where(Post.is_featured == True)
        
        if category:
            query = query.join(Post.category).where(Category.slug == category)
        
        if tag:
            query = query.join(Post.tags).where(Tag.slug == tag)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Post.title.ilike(search_term),
                    Post.excerpt.ilike(search_term),
                    Post.content.ilike(search_term)
                )
            )
        
        query = query.options(
            selectinload(Post.category),
            selectinload(Post.tags)
        )
        query = query.order_by(desc(Post.is_featured), desc(Post.published_at))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        posts = result.scalars().all()
        
        # Convert to response format
        response_posts = []
        for post in posts:
            post_dict = post.to_dict()
            post_dict['category'] = post.category.name if post.category else None
            post_dict['tags'] = [tag.name for tag in post.tags]
            response_posts.append(PostListResponse(**post_dict))
        
        return response_posts
        
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch posts"
        )


@router.get("/posts/{slug}", response_model=PostResponse)
async def get_post(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a specific blog post by slug"""
    try:
        query = select(Post).where(
            Post.slug == slug,
            Post.status == PostStatus.PUBLISHED,
            Post.published_at <= datetime.utcnow()
        ).options(
            selectinload(Post.category),
            selectinload(Post.tags)
        )
        
        result = await db.execute(query)
        post = result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Increment view count
        post.view_count += 1
        await db.commit()
        
        # Convert to response format
        post_dict = post.to_dict()
        post_dict['category'] = post.category.name if post.category else None
        post_dict['tags'] = [tag.name for tag in post.tags]
        
        return PostResponse(**post_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch post"
        )


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all blog categories"""
    try:
        query = select(Category).order_by(Category.name)
        result = await db.execute(query)
        categories = result.scalars().all()
        
        return [CategoryResponse.from_orm(category) for category in categories]
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )


@router.get("/tags", response_model=List[TagResponse])
async def get_tags(db: AsyncSession = Depends(get_db)):
    """Get all blog tags"""
    try:
        query = select(Tag).order_by(desc(Tag.post_count), Tag.name)
        result = await db.execute(query)
        tags = result.scalars().all()
        
        return [TagResponse.from_orm(tag) for tag in tags]
        
    except Exception as e:
        logger.error(f"Error fetching tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tags"
        )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(post_id: str, db: AsyncSession = Depends(get_db)):
    """Get approved comments for a post"""
    try:
        query = select(Comment).where(
            Comment.post_id == post_id,
            Comment.status == CommentStatus.APPROVED,
            Comment.parent_id.is_(None)  # Top-level comments only
        ).order_by(Comment.created_at)
        
        result = await db.execute(query)
        comments = result.scalars().all()
        
        # Get nested comments
        response_comments = []
        for comment in comments:
            comment_dict = comment.to_dict()
            
            # Get children comments
            children_query = select(Comment).where(
                Comment.parent_id == comment.id,
                Comment.status == CommentStatus.APPROVED
            ).order_by(Comment.created_at)
            
            children_result = await db.execute(children_query)
            children = children_result.scalars().all()
            comment_dict['children'] = [CommentResponse.from_orm(child) for child in children]
            
            response_comments.append(CommentResponse(**comment_dict))
        
        return response_comments
        
    except Exception as e:
        logger.error(f"Error fetching comments for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch comments"
        )


@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: str,
    comment_data: CreateCommentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new comment on a post"""
    try:
        # Verify post exists and allows comments
        post_query = select(Post).where(
            Post.id == post_id,
            Post.status == PostStatus.PUBLISHED,
            Post.allow_comments == True
        )
        
        post_result = await db.execute(post_query)
        post = post_result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found or comments not allowed"
            )
        
        # Create comment
        comment = Comment(
            post_id=post_id,
            parent_id=comment_data.parent_id,
            author_name=comment_data.author_name,
            author_email=comment_data.author_email,
            author_website=comment_data.author_website,
            content=comment_data.content,
            html_content=render_markdown(comment_data.content),
            status=CommentStatus.PENDING  # Requires moderation
        )
        
        db.add(comment)
        await db.commit()
        
        return {
            "message": "Comment submitted successfully. It will be visible after moderation.",
            "comment_id": comment.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment"
        )


# Admin endpoints (require API key)
@router.post("/posts/{post_id}/ai-suggestions")
async def get_post_ai_suggestions(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_api_key)
):
    """Get AI-powered suggestions for a blog post"""
    try:
        query = select(Post).where(Post.id == post_id)
        result = await db.execute(query)
        post = result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Get AI suggestions
        suggestions = await get_ai_suggestions(post.title, post.content)
        seo_analysis = await analyze_seo(post.title, post.content, post.meta_description)
        
        # Store suggestions in post
        post.ai_suggestions = {
            "suggestions": suggestions,
            "seo_analysis": seo_analysis,
            "generated_at": datetime.utcnow().isoformat()
        }
        post.seo_score = seo_analysis.get("score", 0)
        post.readability_score = suggestions.get("readability_score", 0)
        
        await db.commit()
        
        return {
            "suggestions": suggestions,
            "seo_analysis": seo_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI suggestions for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI suggestions"
        )


@router.get("/rss")
async def get_rss_feed(db: AsyncSession = Depends(get_db)):
    """Generate RSS feed for blog posts"""
    try:
        # Get latest 20 published posts
        query = select(Post).where(
            Post.status == PostStatus.PUBLISHED,
            Post.published_at <= datetime.utcnow()
        ).options(
            selectinload(Post.category),
            selectinload(Post.tags)
        ).order_by(desc(Post.published_at)).limit(20)
        
        result = await db.execute(query)
        posts = result.scalars().all()
        
        # Generate RSS XML (simplified)
        rss_items = []
        for post in posts:
            rss_items.append({
                "title": post.title,
                "link": f"/blog/{post.slug}",
                "description": post.excerpt or post.title,
                "pub_date": post.published_at.isoformat(),
                "guid": post.id
            })
        
        return {"items": rss_items}
        
    except Exception as e:
        logger.error(f"Error generating RSS feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate RSS feed"
        )