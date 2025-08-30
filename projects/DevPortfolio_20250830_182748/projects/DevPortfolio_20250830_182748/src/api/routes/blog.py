from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from typing import List, Optional
import re
from datetime import datetime

from src.core.database import get_db, redis_client
from src.core.auth import get_current_user, get_current_admin_user, get_optional_user
from src.models.models import BlogPost, User, Comment
from src.schemas.schemas import (
    BlogPostCreate, BlogPostUpdate, BlogPostResponse, BlogPostSummary,
    CommentCreate, CommentResponse,
    AIContentRequest, AIContentResponse,
    SearchQuery, SearchResult
)
from src.services.integrations import APIIntegrationService

router = APIRouter()
integration_service = APIIntegrationService()

def estimate_read_time(content: str) -> int:
    """Estimate reading time based on word count (average 200 words per minute)"""
    word_count = len(content.split())
    return max(1, round(word_count / 200))

def generate_excerpt(content: str, max_length: int = 160) -> str:
    """Generate excerpt from content"""
    # Remove markdown and HTML tags
    clean_content = re.sub(r'[#*`\[\]()_~]', '', content)
    clean_content = re.sub(r'<[^>]+>', '', clean_content)
    
    if len(clean_content) <= max_length:
        return clean_content
    
    # Find the last complete sentence within the limit
    truncated = clean_content[:max_length]
    last_sentence = truncated.rfind('.')
    if last_sentence > max_length * 0.7:  # If we have a good sentence break
        return truncated[:last_sentence + 1]
    
    return truncated.rstrip() + "..."

@router.get("/posts", response_model=List[BlogPostSummary])
async def get_blog_posts(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    published_only: bool = Query(True),
    limit: int = Query(10, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get blog posts with filtering and pagination"""
    query = select(BlogPost)
    
    # Apply filters
    filters = []
    
    if published_only and (not current_user or not current_user.is_admin):
        filters.append(BlogPost.status == "published")
    
    if category:
        filters.append(BlogPost.category == category)
    
    if tag:
        filters.append(BlogPost.tags.contains([tag]))
    
    if featured_only:
        filters.append(BlogPost.is_featured == True)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return posts

@router.get("/posts/{slug}", response_model=BlogPostResponse)
async def get_blog_post(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get a specific blog post by slug"""
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Check if user can view unpublished posts
    if post.status != "published" and (not current_user or not current_user.is_admin):
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Increment view count (only for published posts)
    if post.status == "published":
        await db.execute(
            update(BlogPost)
            .where(BlogPost.id == post.id)
            .values(view_count=BlogPost.view_count + 1)
        )
        await db.commit()
        post.view_count += 1
    
    return post

@router.post("/posts", response_model=BlogPostResponse)
async def create_blog_post(
    post_data: BlogPostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog post"""
    # Check if slug is unique
    existing_post = await db.execute(select(BlogPost).where(BlogPost.slug == post_data.slug))
    if existing_post.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Generate excerpt if not provided
    excerpt = post_data.excerpt or generate_excerpt(post_data.content)
    
    # Calculate read time
    read_time = estimate_read_time(post_data.content)
    
    post = BlogPost(
        **post_data.dict(exclude={"excerpt"}),
        excerpt=excerpt,
        read_time=read_time,
        author_id=current_user.id,
        published_at=datetime.utcnow() if post_data.status == "published" else None
    )
    
    db.add(post)
    await db.commit()
    await db.refresh(post)
    
    return post

@router.put("/posts/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: int,
    post_data: BlogPostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a blog post"""
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    
    # Update fields
    update_data = post_data.dict(exclude_unset=True)
    
    # Recalculate read time if content changed
    if "content" in update_data:
        update_data["read_time"] = estimate_read_time(update_data["content"])
    
    # Set published_at if status changed to published
    if "status" in update_data and update_data["status"] == "published" and not post.published_at:
        update_data["published_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(post, field, value)
    
    await db.commit()
    await db.refresh(post)
    
    return post

@router.delete("/posts/{post_id}")
async def delete_blog_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog post"""
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    await db.delete(post)
    await db.commit()
    
    return {"message": "Blog post deleted successfully"}

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: int,
    approved_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get comments for a blog post"""
    # Verify post exists
    post_result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    query = select(Comment).where(Comment.blog_post_id == post_id)
    
    # Filter approved comments for non-admin users
    if approved_only and (not current_user or not current_user.is_admin):
        query = query.where(Comment.is_approved == True)
    
    query = query.order_by(Comment.created_at.asc())
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    return comments

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new comment on a blog post"""
    # Verify post exists and is published
    post_result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = post_result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    if post.status != "published":
        raise HTTPException(status_code=400, detail="Cannot comment on unpublished posts")
    
    comment = Comment(
        **comment_data.dict(),
        blog_post_id=post_id,
        is_approved=False  # Comments need approval by default
    )
    
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    return comment

@router.post("/ai/generate-content", response_model=AIContentResponse)
async def generate_ai_content(
    request: AIContentRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered content suggestions"""
    try:
        # Customize prompt based on content type
        if request.content_type == "blog_post":
            enhanced_prompt = f"Write a professional technical blog post about: {request.prompt}"
        elif request.content_type == "project_description":
            enhanced_prompt = f"Write a compelling project description for: {request.prompt}"
        elif request.content_type == "bio":
            enhanced_prompt = f"Write a professional bio for a developer: {request.prompt}"
        else:
            enhanced_prompt = request.prompt
        
        generated_content = integration_service.generate_ai_content(
            enhanced_prompt, 
            request.max_tokens
        )
        
        # Generate additional suggestions
        suggestions_prompt = f"Generate 3 SEO-friendly title suggestions for: {request.prompt}"
        suggestions_content = integration_service.generate_ai_content(suggestions_prompt, 100)
        suggestions = [s.strip() for s in suggestions_content.split('\n') if s.strip()]
        
        return AIContentResponse(
            generated_content=generated_content,
            suggestions=suggestions[:3]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI content generation failed: {str(e)}")

@router.get("/search", response_model=List[SearchResult])
async def search_content(
    q: str = Query(..., min_length=2),
    category: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search blog posts and projects"""
    search_term = f"%{q.lower()}%"
    results = []
    
    # Search blog posts
    blog_query = select(BlogPost).where(
        and_(
            BlogPost.status == "published",
            or_(
                func.lower(BlogPost.title).like(search_term),
                func.lower(BlogPost.content).like(search_term),
                func.lower(BlogPost.excerpt).like(search_term)
            )
        )
    )
    
    if category:
        blog_query = blog_query.where(BlogPost.category == category)
    
    blog_result = await db.execute(blog_query.limit(limit // 2))
    blog_posts = blog_result.scalars().all()
    
    for post in blog_posts:
        results.append(SearchResult(
            type="blog_post",
            id=post.id,
            title=post.title,
            description=post.excerpt or "",
            url=f"/blog/{post.slug}",
            relevance_score=1.0  # Simple relevance for now
        ))
    
    return results[:limit]

@router.get("/categories")
async def get_blog_categories(db: AsyncSession = Depends(get_db)):
    """Get all blog post categories"""
    result = await db.execute(
        select(BlogPost.category, func.count(BlogPost.id).label('count'))
        .where(and_(BlogPost.category.isnot(None), BlogPost.status == "published"))
        .group_by(BlogPost.category)
        .order_by(func.count(BlogPost.id).desc())
    )
    
    categories = [{"name": row.category, "count": row.count} for row in result]
    return {"categories": categories}

@router.get("/tags")
async def get_blog_tags(db: AsyncSession = Depends(get_db)):
    """Get all blog post tags"""
    # This is a simplified version - in production, you'd want to properly aggregate JSON array fields
    result = await db.execute(
        select(BlogPost.tags)
        .where(and_(BlogPost.tags.isnot(None), BlogPost.status == "published"))
    )
    
    all_tags = {}
    for row in result:
        if row.tags:
            for tag in row.tags:
                all_tags[tag] = all_tags.get(tag, 0) + 1
    
    tags = [{"name": tag, "count": count} for tag, count in sorted(all_tags.items(), key=lambda x: x[1], reverse=True)]
    return {"tags": tags}