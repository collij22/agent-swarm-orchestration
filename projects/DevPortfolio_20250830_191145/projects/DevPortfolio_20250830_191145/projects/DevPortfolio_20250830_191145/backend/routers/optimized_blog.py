"""
Optimized Blog Router
High-performance blog endpoints with caching and pagination
Target: <200ms response times
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
import asyncio
import time
import logging
from datetime import datetime, timedelta

from database.config import get_db, external_api_cache
from models.optimized import BlogPost, Comment, Analytics
from middleware.performance import get_performance_monitor
from services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for responses
from pydantic import BaseModel

class BlogPostResponse(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: str
    content: Optional[str] = None
    status: str
    featured: bool
    tags: List[str]
    categories: List[str]
    published_at: Optional[datetime]
    view_count: int
    read_time: Optional[int]
    seo_score: int
    
    class Config:
        from_attributes = True

class BlogListResponse(BaseModel):
    posts: List[BlogPostResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool
    total_pages: int

class BlogStatsResponse(BaseModel):
    total_posts: int
    published_posts: int
    total_views: int
    avg_read_time: float
    popular_tags: List[Dict[str, Any]]


@router.get("/posts", response_model=BlogListResponse)
async def get_blog_posts(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Posts per page"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    category: Optional[str] = Query(None, description="Filter by category"),
    featured: Optional[bool] = Query(None, description="Filter featured posts"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated blog posts with optimized queries
    Implements caching and efficient pagination
    """
    start_time = time.time()
    
    # Generate cache key
    cache_key = f"blog_posts:{page}:{limit}:{tag}:{category}:{featured}:{search}"
    
    # Try cache first
    cached_result = await external_api_cache.get("blog", cache_key)
    if cached_result:
        logger.debug(f"Blog posts cache hit: {cache_key}")
        return cached_result
    
    try:
        # Build optimized query
        query = select(BlogPost).where(BlogPost.status == "published")
        count_query = select(func.count(BlogPost.id)).where(BlogPost.status == "published")
        
        # Apply filters
        filters = []
        
        if tag:
            filters.append(BlogPost.tags.contains([tag]))
        
        if category:
            filters.append(BlogPost.categories.contains([category]))
        
        if featured is not None:
            filters.append(BlogPost.featured == featured)
        
        if search:
            search_filter = or_(
                BlogPost.title.ilike(f"%{search}%"),
                BlogPost.content.ilike(f"%{search}%"),
                BlogPost.excerpt.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Order by published date (most recent first)
        query = query.order_by(BlogPost.published_at.desc())
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # Execute queries concurrently
        posts_task = db.execute(query)
        count_task = db.execute(count_query)
        
        posts_result, count_result = await asyncio.gather(posts_task, count_task)
        
        posts = posts_result.scalars().all()
        total = count_result.scalar()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        # Convert to response model
        post_responses = [
            BlogPostResponse(
                id=str(post.id),
                title=post.title,
                slug=post.slug,
                excerpt=post.excerpt,
                status=post.status,
                featured=post.featured,
                tags=post.tags or [],
                categories=post.categories or [],
                published_at=post.published_at,
                view_count=post.view_count,
                read_time=post.read_time,
                seo_score=post.seo_score,
            )
            for post in posts
        ]
        
        result = BlogListResponse(
            posts=post_responses,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev,
            total_pages=total_pages,
        )
        
        # Cache result for 5 minutes
        await external_api_cache.set("blog", cache_key, result.dict())
        
        # Log performance
        response_time = (time.time() - start_time) * 1000
        logger.info(f"Blog posts query completed in {response_time:.2f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching blog posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch blog posts")


@router.get("/posts/{slug}", response_model=BlogPostResponse)
async def get_blog_post(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get individual blog post with full content
    Implements aggressive caching for individual posts
    """
    start_time = time.time()
    
    # Try cache first
    cache_key = f"blog_post:{slug}"
    cached_result = await external_api_cache.get("blog", cache_key)
    if cached_result:
        # Increment view count asynchronously
        asyncio.create_task(increment_view_count(slug, db))
        return cached_result
    
    try:
        # Optimized query with eager loading
        query = select(BlogPost).where(
            and_(
                BlogPost.slug == slug,
                BlogPost.status == "published"
            )
        ).options(
            selectinload(BlogPost.comments)  # Eager load comments if needed
        )
        
        result = await db.execute(query)
        post = result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        # Convert to response
        response = BlogPostResponse(
            id=str(post.id),
            title=post.title,
            slug=post.slug,
            excerpt=post.excerpt,
            content=post.content,  # Include full content for individual post
            status=post.status,
            featured=post.featured,
            tags=post.tags or [],
            categories=post.categories or [],
            published_at=post.published_at,
            view_count=post.view_count,
            read_time=post.read_time,
            seo_score=post.seo_score,
        )
        
        # Cache for 15 minutes (individual posts change less frequently)
        await external_api_cache.set("blog", cache_key, response.dict())
        
        # Increment view count asynchronously
        asyncio.create_task(increment_view_count(slug, db))
        
        # Log performance
        response_time = (time.time() - start_time) * 1000
        logger.info(f"Blog post query completed in {response_time:.2f}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog post {slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch blog post")


@router.get("/stats", response_model=BlogStatsResponse)
async def get_blog_stats(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get blog statistics with aggressive caching
    """
    start_time = time.time()
    
    # Try cache first
    cache_key = "blog_stats"
    cached_result = await external_api_cache.get("blog", cache_key)
    if cached_result:
        return cached_result
    
    try:
        # Optimized aggregation queries
        stats_queries = [
            select(func.count(BlogPost.id)).where(BlogPost.status.in_(["published", "draft"])),
            select(func.count(BlogPost.id)).where(BlogPost.status == "published"),
            select(func.sum(BlogPost.view_count)).where(BlogPost.status == "published"),
            select(func.avg(BlogPost.read_time)).where(BlogPost.status == "published"),
        ]
        
        # Execute all queries concurrently
        results = await asyncio.gather(*[db.execute(query) for query in stats_queries])
        
        total_posts = results[0].scalar() or 0
        published_posts = results[1].scalar() or 0
        total_views = results[2].scalar() or 0
        avg_read_time = results[3].scalar() or 0
        
        # Get popular tags (separate query for complexity)
        tag_query = select(
            func.unnest(BlogPost.tags).label("tag"),
            func.count().label("count")
        ).where(
            BlogPost.status == "published"
        ).group_by(
            func.unnest(BlogPost.tags)
        ).order_by(
            func.count().desc()
        ).limit(10)
        
        tag_result = await db.execute(tag_query)
        popular_tags = [
            {"tag": row.tag, "count": row.count}
            for row in tag_result.fetchall()
        ]
        
        result = BlogStatsResponse(
            total_posts=total_posts,
            published_posts=published_posts,
            total_views=int(total_views),
            avg_read_time=float(avg_read_time),
            popular_tags=popular_tags,
        )
        
        # Cache for 10 minutes
        await external_api_cache.set("blog", cache_key, result.dict())
        
        # Log performance
        response_time = (time.time() - start_time) * 1000
        logger.info(f"Blog stats query completed in {response_time:.2f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching blog stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch blog statistics")


async def increment_view_count(slug: str, db: AsyncSession):
    """
    Asynchronously increment view count without blocking response
    """
    try:
        # Use raw SQL for maximum performance
        await db.execute(
            text("UPDATE blog_posts SET view_count = view_count + 1 WHERE slug = :slug"),
            {"slug": slug}
        )
        await db.commit()
        
        # Also record analytics event
        await record_analytics_event(slug, "page_view", db)
        
    except Exception as e:
        logger.warning(f"Failed to increment view count for {slug}: {e}")


async def record_analytics_event(path: str, event_type: str, db: AsyncSession):
    """
    Record analytics event asynchronously
    """
    try:
        analytics_entry = Analytics(
            path=path,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            date=datetime.utcnow().date(),
        )
        db.add(analytics_entry)
        await db.commit()
        
    except Exception as e:
        logger.warning(f"Failed to record analytics event: {e}")


@router.get("/performance")
async def get_blog_performance():
    """
    Get blog performance metrics
    """
    monitor = get_performance_monitor()
    return monitor.get_performance_summary()