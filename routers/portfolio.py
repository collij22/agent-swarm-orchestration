"""
Portfolio router for project showcase system
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.portfolio import Project, Technology, Skill, Experience
from utils.security import verify_api_key, get_current_user
from utils.github import sync_github_repo
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Pydantic schemas
from pydantic import BaseModel, Field
from typing import Dict, Any


class ProjectResponse(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    short_description: Optional[str]
    featured_image: Optional[str]
    live_url: Optional[str]
    github_url: Optional[str]
    is_featured: bool
    is_published: bool
    status: str
    view_count: int
    like_count: int
    technologies: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TechnologyResponse(BaseModel):
    id: str
    name: str
    category: str
    icon_url: Optional[str]
    color: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class SkillResponse(BaseModel):
    id: str
    technology: TechnologyResponse
    proficiency_level: int
    years_experience: int
    description: Optional[str]
    is_primary: bool
    is_learning: bool

    class Config:
        from_attributes = True


class ExperienceResponse(BaseModel):
    id: str
    company: str
    position: str
    company_url: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    is_current: bool
    description: str
    achievements: Optional[List[str]]
    location: Optional[str]
    employment_type: Optional[str]
    technologies_used: Optional[List[str]]

    class Config:
        from_attributes = True


# Public endpoints
@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    technology: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get published projects with optional filtering"""
    try:
        query = select(Project).where(Project.is_published == True)
        
        if featured_only:
            query = query.where(Project.is_featured == True)
        
        if category:
            query = query.where(Project.category == category)
        
        if technology:
            # Join with technologies to filter by technology name
            query = query.join(Project.technologies).where(Technology.name.ilike(f"%{technology}%"))
        
        query = query.options(selectinload(Project.technologies))
        query = query.order_by(desc(Project.is_featured), desc(Project.created_at))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        projects = result.scalars().all()
        
        # Convert to response format
        response_projects = []
        for project in projects:
            project_dict = project.to_dict()
            project_dict['technologies'] = [tech.name for tech in project.technologies]
            response_projects.append(ProjectResponse(**project_dict))
        
        return response_projects
        
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch projects"
        )


@router.get("/projects/{slug}", response_model=ProjectResponse)
async def get_project(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a specific project by slug"""
    try:
        query = select(Project).where(
            Project.slug == slug,
            Project.is_published == True
        ).options(selectinload(Project.technologies))
        
        result = await db.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Increment view count
        project.view_count += 1
        await db.commit()
        
        # Convert to response format
        project_dict = project.to_dict()
        project_dict['technologies'] = [tech.name for tech in project.technologies]
        
        return ProjectResponse(**project_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project"
        )


@router.get("/technologies", response_model=List[TechnologyResponse])
async def get_technologies(db: AsyncSession = Depends(get_db)):
    """Get all technologies"""
    try:
        query = select(Technology).order_by(Technology.category, Technology.name)
        result = await db.execute(query)
        technologies = result.scalars().all()
        
        return [TechnologyResponse.from_orm(tech) for tech in technologies]
        
    except Exception as e:
        logger.error(f"Error fetching technologies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch technologies"
        )


@router.get("/skills", response_model=List[SkillResponse])
async def get_skills(
    primary_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get skills with proficiency levels"""
    try:
        query = select(Skill).options(selectinload(Skill.technology))
        
        if primary_only:
            query = query.where(Skill.is_primary == True)
        
        query = query.order_by(desc(Skill.proficiency_level), Skill.technology.has(Technology.name))
        
        result = await db.execute(query)
        skills = result.scalars().all()
        
        return [SkillResponse.from_orm(skill) for skill in skills]
        
    except Exception as e:
        logger.error(f"Error fetching skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch skills"
        )


@router.get("/experience", response_model=List[ExperienceResponse])
async def get_experience(db: AsyncSession = Depends(get_db)):
    """Get work experience timeline"""
    try:
        query = select(Experience).order_by(desc(Experience.is_current), desc(Experience.start_date))
        result = await db.execute(query)
        experiences = result.scalars().all()
        
        return [ExperienceResponse.from_orm(exp) for exp in experiences]
        
    except Exception as e:
        logger.error(f"Error fetching experience: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch experience"
        )


# Admin endpoints (require API key)
@router.post("/projects/{project_id}/sync-github")
async def sync_project_github(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_api_key)
):
    """Sync project with GitHub repository"""
    try:
        query = select(Project).where(Project.id == project_id)
        result = await db.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if not project.github_repo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no GitHub repository configured"
            )
        
        # Sync with GitHub
        github_data = await sync_github_repo(project.github_repo)
        project.github_data = github_data
        project.github_last_sync = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "GitHub sync completed", "data": github_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing GitHub for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync with GitHub"
        )


@router.post("/projects/{project_id}/increment-views")
async def increment_project_views(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Increment project view count (for analytics)"""
    try:
        query = select(Project).where(Project.id == project_id)
        result = await db.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project.view_count += 1
        await db.commit()
        
        return {"view_count": project.view_count}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error incrementing views for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update view count"
        )