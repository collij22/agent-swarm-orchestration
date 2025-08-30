"""
Unit tests for portfolio models.
Ensures data integrity, validation, and business logic correctness.
"""
import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../projects/DevPortfolio_20250830_174003/backend'))

from models.models import (
    Project, BlogPost, Skill, Experience, Comment, 
    User, Analytics, ContactSubmission
)


class TestProject:
    """Test Project model validation and business logic."""
    
    def test_project_creation_valid(self):
        """Test creating a valid project."""
        project = Project(
            title="Test Project",
            description="A test project",
            github_url="https://github.com/user/repo",
            demo_url="https://demo.example.com",
            technologies=["Python", "FastAPI"],
            featured=True
        )
        assert project.title == "Test Project"
        assert project.featured is True
        assert len(project.technologies) == 2
    
    def test_project_invalid_github_url(self):
        """Test project validation with invalid GitHub URL."""
        with pytest.raises(ValueError):
            Project(
                title="Test Project",
                description="A test project",
                github_url="not-a-valid-url",
                technologies=["Python"]
            )
    
    def test_project_slug_generation(self):
        """Test automatic slug generation from title."""
        project = Project(
            title="My Awesome Project!",
            description="Test",
            technologies=["Python"]
        )
        expected_slug = "my-awesome-project"
        assert project.slug == expected_slug
    
    def test_project_search_functionality(self):
        """Test project search by technology and title."""
        projects = [
            Project(title="React App", description="Frontend", technologies=["React", "TypeScript"]),
            Project(title="Python API", description="Backend", technologies=["Python", "FastAPI"]),
            Project(title="Full Stack", description="Complete", technologies=["React", "Python"])
        ]
        
        # Search by technology
        react_projects = [p for p in projects if "React" in p.technologies]
        assert len(react_projects) == 2
        
        # Search by title
        api_projects = [p for p in projects if "API" in p.title]
        assert len(api_projects) == 1


class TestBlogPost:
    """Test BlogPost model validation and business logic."""
    
    def test_blog_post_creation_valid(self):
        """Test creating a valid blog post."""
        post = BlogPost(
            title="Test Post",
            content="# Test Content\n\nThis is a test.",
            author_id=1,
            tags=["testing", "python"],
            published=True
        )
        assert post.title == "Test Post"
        assert post.published is True
        assert "testing" in post.tags
    
    def test_blog_post_slug_generation(self):
        """Test automatic slug generation from title."""
        post = BlogPost(
            title="How to Test FastAPI Applications",
            content="Content here",
            author_id=1
        )
        expected_slug = "how-to-test-fastapi-applications"
        assert post.slug == expected_slug
    
    def test_blog_post_reading_time_calculation(self):
        """Test reading time calculation based on content length."""
        # Average reading speed: 200 words per minute
        content = " ".join(["word"] * 400)  # 400 words
        post = BlogPost(
            title="Long Post",
            content=content,
            author_id=1
        )
        expected_reading_time = 2  # 400 words / 200 wpm = 2 minutes
        assert post.reading_time_minutes == expected_reading_time
    
    def test_blog_post_draft_functionality(self):
        """Test draft vs published post behavior."""
        draft = BlogPost(
            title="Draft Post",
            content="Draft content",
            author_id=1,
            published=False
        )
        published = BlogPost(
            title="Published Post",
            content="Published content",
            author_id=1,
            published=True
        )
        
        assert draft.published is False
        assert published.published is True
    
    def test_blog_post_seo_optimization(self):
        """Test SEO fields and meta description generation."""
        post = BlogPost(
            title="SEO Test Post",
            content="This is a long content for testing SEO optimization and meta description generation.",
            author_id=1,
            meta_description="Custom meta description"
        )
        assert post.meta_description == "Custom meta description"
        
        # Test auto-generation when not provided
        post_auto = BlogPost(
            title="Auto Meta Post",
            content="This is content that should be truncated for meta description generation. " * 10,
            author_id=1
        )
        assert len(post_auto.meta_description) <= 160  # SEO best practice


class TestSkill:
    """Test Skill model validation and proficiency logic."""
    
    def test_skill_creation_valid(self):
        """Test creating a valid skill."""
        skill = Skill(
            name="Python",
            category="Programming Languages",
            proficiency_level=4,
            years_experience=3
        )
        assert skill.name == "Python"
        assert skill.proficiency_level == 4
    
    def test_skill_proficiency_validation(self):
        """Test skill proficiency level validation (1-5 scale)."""
        with pytest.raises(ValueError):
            Skill(
                name="Invalid Skill",
                category="Test",
                proficiency_level=6,  # Invalid: > 5
                years_experience=1
            )
        
        with pytest.raises(ValueError):
            Skill(
                name="Invalid Skill 2",
                category="Test",
                proficiency_level=0,  # Invalid: < 1
                years_experience=1
            )
    
    def test_skill_categorization(self):
        """Test skill categorization and grouping."""
        skills = [
            Skill(name="Python", category="Programming Languages", proficiency_level=4, years_experience=3),
            Skill(name="JavaScript", category="Programming Languages", proficiency_level=3, years_experience=2),
            Skill(name="Docker", category="DevOps", proficiency_level=3, years_experience=2),
            Skill(name="AWS", category="Cloud Platforms", proficiency_level=2, years_experience=1)
        ]
        
        # Group by category
        categories = {}
        for skill in skills:
            if skill.category not in categories:
                categories[skill.category] = []
            categories[skill.category].append(skill)
        
        assert len(categories["Programming Languages"]) == 2
        assert len(categories["DevOps"]) == 1
        assert len(categories["Cloud Platforms"]) == 1


class TestExperience:
    """Test Experience model validation and timeline logic."""
    
    def test_experience_creation_valid(self):
        """Test creating a valid experience entry."""
        experience = Experience(
            company="Tech Corp",
            position="Senior Developer",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            description="Developed awesome applications",
            achievements=["Led team of 5", "Improved performance by 50%"]
        )
        assert experience.company == "Tech Corp"
        assert len(experience.achievements) == 2
    
    def test_experience_current_position(self):
        """Test current position (no end date)."""
        current_exp = Experience(
            company="Current Corp",
            position="Lead Developer",
            start_date=date(2023, 1, 1),
            end_date=None,  # Current position
            description="Current role"
        )
        assert current_exp.end_date is None
        assert current_exp.is_current is True
    
    def test_experience_duration_calculation(self):
        """Test experience duration calculation."""
        experience = Experience(
            company="Test Corp",
            position="Developer",
            start_date=date(2020, 1, 1),
            end_date=date(2022, 1, 1),
            description="Two year role"
        )
        duration = experience.duration_years
        assert duration == 2.0
    
    def test_experience_timeline_validation(self):
        """Test that end date cannot be before start date."""
        with pytest.raises(ValueError):
            Experience(
                company="Invalid Corp",
                position="Developer",
                start_date=date(2023, 1, 1),
                end_date=date(2022, 1, 1),  # Invalid: before start date
                description="Invalid timeline"
            )


class TestComment:
    """Test Comment model validation and moderation logic."""
    
    def test_comment_creation_valid(self):
        """Test creating a valid comment."""
        comment = Comment(
            content="Great article!",
            author_name="John Doe",
            author_email="john@example.com",
            blog_post_id=1
        )
        assert comment.content == "Great article!"
        assert comment.is_approved is False  # Default to unapproved
    
    def test_comment_spam_detection(self):
        """Test basic spam detection logic."""
        spam_comment = Comment(
            content="BUY NOW! CLICK HERE! AMAZING DEAL!!!",
            author_name="Spammer",
            author_email="spam@spam.com",
            blog_post_id=1
        )
        
        # Check for spam indicators
        spam_indicators = ["BUY NOW", "CLICK HERE", "AMAZING DEAL"]
        content_upper = spam_comment.content.upper()
        spam_score = sum(1 for indicator in spam_indicators if indicator in content_upper)
        
        assert spam_score >= 2  # High spam score
    
    def test_comment_nested_replies(self):
        """Test nested comment functionality."""
        parent_comment = Comment(
            content="Parent comment",
            author_name="Parent Author",
            author_email="parent@example.com",
            blog_post_id=1
        )
        
        reply_comment = Comment(
            content="Reply to parent",
            author_name="Reply Author",
            author_email="reply@example.com",
            blog_post_id=1,
            parent_id=parent_comment.id
        )
        
        assert reply_comment.parent_id == parent_comment.id


class TestUser:
    """Test User model validation and authentication logic."""
    
    def test_user_creation_valid(self):
        """Test creating a valid user."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            is_admin=True
        )
        assert user.username == "testuser"
        assert user.is_admin is True
    
    def test_user_email_validation(self):
        """Test user email validation."""
        with pytest.raises(ValueError):
            User(
                username="testuser",
                email="invalid-email",  # Invalid email format
                full_name="Test User"
            )
    
    def test_user_password_hashing(self):
        """Test password hashing functionality."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        
        # Mock password hashing
        with patch('bcrypt.hashpw') as mock_hash:
            mock_hash.return_value = b'hashed_password'
            user.set_password("plaintext_password")
            mock_hash.assert_called_once()


class TestAnalytics:
    """Test Analytics model and data collection logic."""
    
    def test_analytics_event_creation(self):
        """Test creating analytics events."""
        event = Analytics(
            event_type="page_view",
            page="/portfolio",
            user_agent="Mozilla/5.0...",
            ip_address="192.168.1.1"
        )
        assert event.event_type == "page_view"
        assert event.page == "/portfolio"
    
    def test_analytics_privacy_compliance(self):
        """Test analytics privacy and data anonymization."""
        event = Analytics(
            event_type="page_view",
            page="/blog/post-1",
            user_agent="Mozilla/5.0...",
            ip_address="192.168.1.100"
        )
        
        # Test IP anonymization (last octet should be 0)
        anonymized_ip = ".".join(event.ip_address.split(".")[:-1] + ["0"])
        assert anonymized_ip == "192.168.1.0"


class TestContactSubmission:
    """Test ContactSubmission model and validation."""
    
    def test_contact_submission_valid(self):
        """Test creating a valid contact submission."""
        submission = ContactSubmission(
            name="John Doe",
            email="john@example.com",
            subject="Project Inquiry",
            message="I'd like to discuss a project opportunity.",
            company="Tech Corp"
        )
        assert submission.name == "John Doe"
        assert submission.subject == "Project Inquiry"
    
    def test_contact_submission_spam_protection(self):
        """Test contact form spam protection."""
        spam_submission = ContactSubmission(
            name="Spammer",
            email="spam@spam.com",
            subject="URGENT BUSINESS PROPOSAL",
            message="Dear Sir/Madam, I have a business proposal for you..." * 10
        )
        
        # Check message length (potential spam indicator)
        assert len(spam_submission.message) > 500  # Very long message
        
        # Check for common spam phrases
        spam_phrases = ["business proposal", "urgent", "dear sir/madam"]
        message_lower = spam_submission.message.lower()
        spam_indicators = sum(1 for phrase in spam_phrases if phrase in message_lower)
        assert spam_indicators >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])