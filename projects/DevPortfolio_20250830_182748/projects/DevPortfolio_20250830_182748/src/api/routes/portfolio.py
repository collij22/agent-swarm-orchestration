from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional

from src.core.database import get_db
from src.core.auth import get_current_user, get_current_admin_user, get_optional_user
from src.models.models import Project, User, Skill, Experience
from src.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    SkillCreate, SkillUpdate, SkillResponse,
    ExperienceCreate, ExperienceUpdate, ExperienceResponse,
    UserProfile
)
from src.services.integrations import APIIntegrationService

router = APIRouter()
integration_service = APIIntegrationService()

@router.get("/profile/{username}", response_model=UserProfile)
async def get_user_profile(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """Get public user profile with portfolio data"""
    # Get user
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get counts
    projects_result = await db.execute(
        select(Project).where(and_(Project.owner_id == user.id, Project.status == "active"))
    )
    projects_count = len(projects_result.scalars().all())
    
    # Convert to response model
    profile = UserProfile.from_orm(user)
    profile.projects_count = projects_count
    
    return profile

@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    username: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    limit: int = Query(10, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """Get projects with optional filtering"""
    query = select(Project)
    
    # Filter by username if provided
    if username:
        user_result = await db.execute(select(User).where(User.username == username))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        query = query.where(Project.owner_id == user.id)
    
    # Apply filters
    filters = [Project.status.in_(["active", "featured"])]
    
    if category:
        filters.append(Project.category == category)
    
    if featured_only:
        filters.append(Project.is_featured == True)
    
    query = query.where(and_(*filters))
    query = query.order_by(Project.order_index, Project.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return projects

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project by ID"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    project = Project(
        **project_data.dict(),
        owner_id=current_user.id
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project

@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")
    
    # Update fields
    for field, value in project_data.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}

@router.get("/skills", response_model=List[SkillResponse])
async def get_skills(
    username: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get skills with optional filtering"""
    query = select(Skill)
    
    # Filter by username if provided
    if username:
        user_result = await db.execute(select(User).where(User.username == username))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        query = query.where(Skill.user_id == user.id)
    
    # Apply filters
    filters = []
    
    if category:
        filters.append(Skill.category == category)
    
    if featured_only:
        filters.append(Skill.is_featured == True)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Skill.order_index, Skill.proficiency.desc())
    
    result = await db.execute(query)
    skills = result.scalars().all()
    
    return skills

@router.post("/skills", response_model=SkillResponse)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new skill"""
    skill = Skill(
        **skill_data.dict(),
        user_id=current_user.id
    )
    
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    
    return skill

@router.get("/experiences", response_model=List[ExperienceResponse])
async def get_experiences(
    username: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get work experiences"""
    query = select(Experience)
    
    # Filter by username if provided
    if username:
        user_result = await db.execute(select(User).where(User.username == username))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        query = query.where(Experience.user_id == user.id)
    
    query = query.order_by(Experience.order_index, Experience.start_date.desc())
    
    result = await db.execute(query)
    experiences = result.scalars().all()
    
    return experiences

@router.post("/experiences", response_model=ExperienceResponse)
async def create_experience(
    experience_data: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new work experience"""
    experience = Experience(
        **experience_data.dict(),
        user_id=current_user.id
    )
    
    db.add(experience)
    await db.commit()
    await db.refresh(experience)
    
    return experience

@router.get("/github/{username}")
async def get_github_repos(username: str):
    """Get GitHub repositories for a user"""
    try:
        repos = integration_service.get_github_repositories(username)
        return {"repositories": repos}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching GitHub data: {str(e)}")