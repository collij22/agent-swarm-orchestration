"""
Portfolio Router - Project Showcase System
Handles project display, GitHub integration, and portfolio management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
import logging

from database.connection import get_database
from models.models import Project, Skill, Experience
from services.github_service import GitHubService
from services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for API responses
class ProjectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    short_description: Optional[str]
    github_url: Optional[str]
    demo_url: Optional[str]
    image_url: Optional[str]
    technologies: List[str]
    category: Optional[str]
    status: str
    is_featured: bool
    view_count: int
    github_stars: int
    github_forks: int
    created_at: str
    
    class Config:
        from_attributes = True

class SkillResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    proficiency_level: int
    years_experience: Optional[float]
    description: Optional[str]
    icon_url: Optional[str]
    
    class Config:
        from_attributes = True

class ExperienceResponse(BaseModel):
    id: int
    company_name: str
    position: str
    description: Optional[str]
    achievements: List[str]
    start_date: str
    end_date: Optional[str]
    is_current: bool
    company_url: Optional[str]
    company_logo: Optional[str]
    location: Optional[str]
    technologies: List[str]
    
    class Config:
        from_attributes = True

@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    category: Optional[str] = Query(None, description="Filter by category"),
    technology: Optional[str] = Query(None, description="Filter by technology"),
    featured_only: bool = Query(False, description="Show only featured projects"),
    limit: int = Query(20, ge=1, le=100, description="Number of projects to return"),
    offset: int = Query(0, ge=0, description="Number of projects to skip"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get portfolio projects with filtering and pagination
    """
    try:
        # Build query
        query = select(Project).where(Project.status == "active")
        
        if featured_only:
            query = query.where(Project.is_featured == True)
        
        if category:
            query = query.where(Project.category == category)
        
        if technology:
            query = query.where(Project.technologies.contains([technology]))
        
        # Order by featured first, then by sort order
        query = query.order_by(desc(Project.is_featured), Project.sort_order, desc(Project.created_at))
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        projects = result.scalars().all()
        
        # Convert to response format
        project_responses = []
        for project in projects:
            project_dict = {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "short_description": project.short_description,
                "github_url": project.github_url,
                "demo_url": project.demo_url,
                "image_url": project.image_url,
                "technologies": project.technologies or [],
                "category": project.category,
                "status": project.status,
                "is_featured": project.is_featured,
                "view_count": project.view_count,
                "github_stars": project.github_stars,
                "github_forks": project.github_forks,
                "created_at": project.created_at.isoformat() if project.created_at else None
            }
            project_responses.append(ProjectResponse(**project_dict))
        
        return project_responses
        
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch projects"
        )

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_database)
):
    """
    Get a specific project by ID and increment view count
    """
    try:
        # Get project
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Increment view count
        project.view_count += 1
        await db.commit()
        
        # Track analytics
        analytics = AnalyticsService()
        await analytics.track_event("project_view", {
            "project_id": project_id,
            "project_title": project.title
        })
        
        project_dict = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "short_description": project.short_description,
            "github_url": project.github_url,
            "demo_url": project.demo_url,
            "image_url": project.image_url,
            "technologies": project.technologies or [],
            "category": project.category,
            "status": project.status,
            "is_featured": project.is_featured,
            "view_count": project.view_count,
            "github_stars": project.github_stars,
            "github_forks": project.github_forks,
            "created_at": project.created_at.isoformat() if project.created_at else None
        }
        
        return ProjectResponse(**project_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project"
        )

@router.get("/skills", response_model=List[SkillResponse])
async def get_skills(
    category: Optional[str] = Query(None, description="Filter by skill category"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get skills with proficiency levels
    """
    try:
        query = select(Skill).where(Skill.is_active == True)
        
        if category:
            query = query.where(Skill.category == category)
        
        query = query.order_by(Skill.sort_order, desc(Skill.proficiency_level))
        
        result = await db.execute(query)
        skills = result.scalars().all()
        
        skill_responses = []
        for skill in skills:
            skill_dict = {
                "id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "proficiency_level": skill.proficiency_level,
                "years_experience": skill.years_experience,
                "description": skill.description,
                "icon_url": skill.icon_url
            }
            skill_responses.append(SkillResponse(**skill_dict))
        
        return skill_responses
        
    except Exception as e:
        logger.error(f"Error fetching skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch skills"
        )

@router.get("/experience", response_model=List[ExperienceResponse])
async def get_experience(
    db: AsyncSession = Depends(get_database)
):
    """
    Get work experience timeline
    """
    try:
        query = select(Experience).order_by(desc(Experience.start_date))
        result = await db.execute(query)
        experiences = result.scalars().all()
        
        experience_responses = []
        for exp in experiences:
            exp_dict = {
                "id": exp.id,
                "company_name": exp.company_name,
                "position": exp.position,
                "description": exp.description,
                "achievements": exp.achievements or [],
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else None,
                "is_current": exp.is_current,
                "company_url": exp.company_url,
                "company_logo": exp.company_logo,
                "location": exp.location,
                "technologies": exp.technologies or []
            }
            experience_responses.append(ExperienceResponse(**exp_dict))
        
        return experience_responses
        
    except Exception as e:
        logger.error(f"Error fetching experience: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch experience"
        )

@router.get("/stats")
async def get_portfolio_stats(
    db: AsyncSession = Depends(get_database)
):
    """
    Get portfolio statistics
    """
    try:
        # Count projects
        project_count_result = await db.execute(
            select(func.count(Project.id)).where(Project.status == "active")
        )
        project_count = project_count_result.scalar()
        
        # Count skills
        skill_count_result = await db.execute(
            select(func.count(Skill.id)).where(Skill.is_active == True)
        )
        skill_count = skill_count_result.scalar()
        
        # Count years of experience (from earliest start date)
        earliest_exp_result = await db.execute(
            select(func.min(Experience.start_date))
        )
        earliest_date = earliest_exp_result.scalar()
        
        years_experience = 0
        if earliest_date:
            from datetime import datetime
            years_experience = (datetime.now() - earliest_date).days // 365
        
        # Total GitHub stars
        stars_result = await db.execute(
            select(func.sum(Project.github_stars)).where(Project.status == "active")
        )
        total_stars = stars_result.scalar() or 0
        
        return {
            "total_projects": project_count,
            "total_skills": skill_count,
            "years_experience": years_experience,
            "github_stars": total_stars,
            "last_updated": "2024-08-30T17:40:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio statistics"
        )

@router.post("/sync-github")
async def sync_github_projects(
    db: AsyncSession = Depends(get_database)
):
    """
    Sync projects with GitHub repositories (admin only)
    """
    try:
        github_service = GitHubService()
        
        # Get all projects with GitHub URLs
        result = await db.execute(
            select(Project).where(Project.github_url.isnot(None))
        )
        projects = result.scalars().all()
        
        updated_count = 0
        for project in projects:
            try:
                # Extract repo info from URL
                repo_info = github_service.extract_repo_info(project.github_url)
                if repo_info:
                    # Get latest GitHub data
                    github_data = await github_service.get_repository_info(
                        repo_info["owner"], repo_info["repo"]
                    )
                    
                    if github_data:
                        project.github_stars = github_data.get("stargazers_count", 0)
                        project.github_forks = github_data.get("forks_count", 0)
                        project.description = github_data.get("description") or project.description
                        updated_count += 1
                        
            except Exception as e:
                logger.warning(f"Failed to sync project {project.id}: {e}")
                continue
        
        await db.commit()
        
        return {
            "message": f"Successfully synced {updated_count} projects with GitHub",
            "updated_projects": updated_count
        }
        
    except Exception as e:
        logger.error(f"Error syncing GitHub projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync GitHub projects"
        )