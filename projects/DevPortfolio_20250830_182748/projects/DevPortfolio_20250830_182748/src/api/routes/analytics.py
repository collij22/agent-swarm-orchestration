from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from src.core.database import get_db, redis_client
from src.core.auth import get_current_admin_user, get_optional_user
from src.models.models import Analytics, BlogPost, Project, User, Contact
from src.schemas.schemas import AnalyticsEvent, AnalyticsResponse, ContactCreate, ContactResponse

router = APIRouter()

@router.post("/track")
async def track_event(
    event: AnalyticsEvent,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Track analytics event"""
    # Get client information
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else "unknown"
    referrer = request.headers.get("referer", "")
    
    # Create analytics record
    analytics_record = Analytics(
        event_type=event.event_type,
        page_path=event.page_path,
        user_agent=user_agent,
        ip_address=ip_address,
        referrer=referrer,
        metadata=event.metadata or {}
    )
    
    db.add(analytics_record)
    await db.commit()
    
    # Also store in Redis for real-time analytics
    try:
        # Increment page view counter
        if event.event_type == "page_view" and event.page_path:
            redis_client.incr(f"page_views:{event.page_path}")
            redis_client.expire(f"page_views:{event.page_path}", 86400 * 30)  # 30 days
        
        # Track unique visitors (simplified)
        if ip_address != "unknown":
            redis_client.setex(f"visitor:{ip_address}", 86400, "1")  # 24 hours
    except Exception:
        # Redis errors shouldn't break the tracking
        pass
    
    return {"status": "tracked"}

@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics dashboard data (admin only)"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total page views
    total_views_result = await db.execute(
        select(func.count(Analytics.id))
        .where(and_(
            Analytics.event_type == "page_view",
            Analytics.created_at >= start_date
        ))
    )
    total_views = total_views_result.scalar() or 0
    
    # Unique visitors (simplified - based on unique IP addresses)
    unique_visitors_result = await db.execute(
        select(func.count(func.distinct(Analytics.ip_address)))
        .where(and_(
            Analytics.event_type == "page_view",
            Analytics.created_at >= start_date
        ))
    )
    unique_visitors = unique_visitors_result.scalar() or 0
    
    # Popular pages
    popular_pages_result = await db.execute(
        select(
            Analytics.page_path,
            func.count(Analytics.id).label('views')
        )
        .where(and_(
            Analytics.event_type == "page_view",
            Analytics.created_at >= start_date,
            Analytics.page_path.isnot(None)
        ))
        .group_by(Analytics.page_path)
        .order_by(desc('views'))
        .limit(10)
    )
    
    popular_pages = [
        {"page": row.page_path, "views": row.views}
        for row in popular_pages_result
    ]
    
    # Recent activity
    recent_activity_result = await db.execute(
        select(Analytics)
        .where(Analytics.created_at >= start_date)
        .order_by(desc(Analytics.created_at))
        .limit(20)
    )
    
    recent_activity = [
        {
            "event_type": record.event_type,
            "page_path": record.page_path,
            "created_at": record.created_at,
            "metadata": record.metadata
        }
        for record in recent_activity_result.scalars()
    ]
    
    return AnalyticsResponse(
        total_views=total_views,
        unique_visitors=unique_visitors,
        popular_pages=popular_pages,
        recent_activity=recent_activity
    )

@router.get("/blog-stats")
async def get_blog_stats(
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get blog-specific analytics"""
    # Most viewed blog posts
    most_viewed_result = await db.execute(
        select(BlogPost.title, BlogPost.slug, BlogPost.view_count)
        .where(BlogPost.status == "published")
        .order_by(desc(BlogPost.view_count))
        .limit(10)
    )
    
    most_viewed = [
        {
            "title": row.title,
            "slug": row.slug,
            "views": row.view_count
        }
        for row in most_viewed_result
    ]
    
    # Blog post performance by category
    category_stats_result = await db.execute(
        select(
            BlogPost.category,
            func.count(BlogPost.id).label('posts'),
            func.avg(BlogPost.view_count).label('avg_views')
        )
        .where(and_(
            BlogPost.status == "published",
            BlogPost.category.isnot(None)
        ))
        .group_by(BlogPost.category)
        .order_by(desc('avg_views'))
    )
    
    category_stats = [
        {
            "category": row.category,
            "posts": row.posts,
            "avg_views": round(row.avg_views or 0, 1)
        }
        for row in category_stats_result
    ]
    
    return {
        "most_viewed_posts": most_viewed,
        "category_performance": category_stats
    }

@router.get("/realtime")
async def get_realtime_stats(
    admin_user: User = Depends(get_current_admin_user)
):
    """Get real-time analytics from Redis"""
    try:
        # Get current active visitors (simplified)
        active_visitors = len(redis_client.keys("visitor:*"))
        
        # Get today's page views for top pages
        today_views = {}
        for key in redis_client.keys("page_views:*"):
            page_path = key.replace("page_views:", "")
            views = redis_client.get(key)
            today_views[page_path] = int(views) if views else 0
        
        # Sort by views
        top_pages_today = sorted(
            today_views.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "active_visitors": active_visitors,
            "top_pages_today": [
                {"page": page, "views": views}
                for page, views in top_pages_today
            ]
        }
    except Exception as e:
        return {
            "active_visitors": 0,
            "top_pages_today": [],
            "error": "Redis unavailable"
        }

@router.post("/contact", response_model=ContactResponse)
async def submit_contact_form(
    contact_data: ContactCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Submit contact form"""
    # Create contact record
    contact = Contact(
        name=contact_data.name,
        email=contact_data.email,
        subject=contact_data.subject,
        message=contact_data.message
    )
    
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    
    # Track contact form submission
    analytics_record = Analytics(
        event_type="contact_form_submit",
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else "unknown",
        metadata={"contact_id": contact.id}
    )
    db.add(analytics_record)
    await db.commit()
    
    # In a real application, you'd send an email notification here
    
    return contact

@router.get("/contacts")
async def get_contacts(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get contact form submissions (admin only)"""
    query = select(Contact)
    
    if unread_only:
        query = query.where(Contact.is_read == False)
    
    query = query.order_by(desc(Contact.created_at))
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    return {"contacts": contacts}

@router.put("/contacts/{contact_id}/mark-read")
async def mark_contact_read(
    contact_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark contact as read (admin only)"""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.is_read = True
    await db.commit()
    
    return {"message": "Contact marked as read"}

@router.get("/export")
async def export_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("json", regex="^(json|csv)$"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Export analytics data (admin only)"""
    if (end_date - start_date).days > 365:
        raise HTTPException(
            status_code=400, 
            detail="Date range cannot exceed 365 days"
        )
    
    result = await db.execute(
        select(Analytics)
        .where(and_(
            Analytics.created_at >= start_date,
            Analytics.created_at <= end_date
        ))
        .order_by(Analytics.created_at)
    )
    
    records = result.scalars().all()
    
    if format == "csv":
        # In a real application, you'd generate CSV content
        # For demo, return JSON with CSV indication
        return {
            "format": "csv",
            "message": "CSV export would be generated here",
            "record_count": len(records)
        }
    
    return {
        "format": "json",
        "data": [
            {
                "id": record.id,
                "event_type": record.event_type,
                "page_path": record.page_path,
                "user_agent": record.user_agent,
                "ip_address": record.ip_address,
                "referrer": record.referrer,
                "metadata": record.metadata,
                "created_at": record.created_at
            }
            for record in records
        ],
        "record_count": len(records)
    }