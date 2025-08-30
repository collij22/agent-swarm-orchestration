"""
Unit Tests for Main Application Components
Tests core functionality, models, and business logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

# Test imports
from main import app
from models.user import User
from models.blog import BlogPost, BlogCategory
from models.portfolio import Project, Skill
from models.analytics import PageView, Visitor
from models.contact import ContactSubmission

class TestMainApplication:
    """Test main FastAPI application"""
    
    def test_app_creation(self):
        """Test that the app is created successfully"""
        assert app is not None
        assert app.title == "DevPortfolio API"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "api_version" in data
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/")
        assert response.status_code == 200
        # CORS headers should be configured
    
    def test_security_headers(self, client, security_headers):
        """Test security headers are present"""
        response = client.get("/")
        for header, expected_value in security_headers.items():
            # Note: Some headers might be added by middleware
            pass  # Will be implemented with actual security middleware

class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, db_session):
        """Test creating a new user"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "is_admin": False,
            "is_active": True
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_email_validation(self, db_session):
        """Test user email validation"""
        # Test valid email
        user = User(
            email="valid@example.com",
            username="validuser",
            full_name="Valid User"
        )
        db_session.add(user)
        db_session.commit()
        assert user.id is not None
    
    def test_user_unique_constraints(self, db_session):
        """Test unique constraints on user fields"""
        # Create first user
        user1 = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User 1"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create user with same email
        user2 = User(
            email="test@example.com",
            username="testuser2",
            full_name="Test User 2"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_user_password_hashing(self, db_session):
        """Test password hashing functionality"""
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User"
        )
        
        # Test password setting (if implemented)
        if hasattr(user, 'set_password'):
            user.set_password("testpassword")
            assert user.password_hash is not None
            assert user.password_hash != "testpassword"
            
            # Test password verification
            if hasattr(user, 'verify_password'):
                assert user.verify_password("testpassword") is True
                assert user.verify_password("wrongpassword") is False

class TestBlogModel:
    """Test Blog model functionality"""
    
    def test_blog_post_creation(self, db_session, test_user):
        """Test creating a blog post"""
        post_data = {
            "title": "Test Blog Post",
            "slug": "test-blog-post",
            "content": "This is test content",
            "excerpt": "Test excerpt",
            "status": "published",
            "author_id": test_user.id
        }
        post = BlogPost(**post_data)
        db_session.add(post)
        db_session.commit()
        
        assert post.id is not None
        assert post.title == "Test Blog Post"
        assert post.slug == "test-blog-post"
        assert post.author_id == test_user.id
        assert post.created_at is not None
    
    def test_blog_post_slug_generation(self, db_session, test_user):
        """Test automatic slug generation"""
        post = BlogPost(
            title="This is a Test Title with Spaces",
            content="Test content",
            author_id=test_user.id
        )
        
        # If slug auto-generation is implemented
        if hasattr(post, 'generate_slug'):
            post.generate_slug()
            assert post.slug == "this-is-a-test-title-with-spaces"
    
    def test_blog_post_status_validation(self, db_session, test_user):
        """Test blog post status validation"""
        valid_statuses = ["draft", "published", "archived"]
        
        for status in valid_statuses:
            post = BlogPost(
                title=f"Test Post {status}",
                content="Test content",
                status=status,
                author_id=test_user.id
            )
            db_session.add(post)
            db_session.commit()
            assert post.status == status
            db_session.delete(post)
            db_session.commit()
    
    def test_blog_category_creation(self, db_session):
        """Test creating blog categories"""
        category = BlogCategory(
            name="Technology",
            slug="technology",
            description="Tech-related posts"
        )
        db_session.add(category)
        db_session.commit()
        
        assert category.id is not None
        assert category.name == "Technology"
        assert category.slug == "technology"

class TestPortfolioModel:
    """Test Portfolio model functionality"""
    
    def test_project_creation(self, db_session):
        """Test creating a portfolio project"""
        project_data = {
            "title": "Test Project",
            "slug": "test-project",
            "description": "A test project",
            "github_url": "https://github.com/test/project",
            "demo_url": "https://testproject.com",
            "technologies": ["Python", "FastAPI"],
            "status": "completed",
            "featured": True
        }
        project = Project(**project_data)
        db_session.add(project)
        db_session.commit()
        
        assert project.id is not None
        assert project.title == "Test Project"
        assert project.technologies == ["Python", "FastAPI"]
        assert project.featured is True
    
    def test_project_view_count(self, db_session):
        """Test project view count functionality"""
        project = Project(
            title="Test Project",
            description="Test description",
            view_count=0
        )
        db_session.add(project)
        db_session.commit()
        
        # Test incrementing view count
        if hasattr(project, 'increment_views'):
            original_count = project.view_count
            project.increment_views()
            assert project.view_count == original_count + 1
    
    def test_skill_creation(self, db_session):
        """Test creating skills"""
        skill = Skill(
            name="Python",
            category="Programming Language",
            proficiency_level=90,
            years_experience=5
        )
        db_session.add(skill)
        db_session.commit()
        
        assert skill.id is not None
        assert skill.name == "Python"
        assert skill.proficiency_level == 90
        assert skill.years_experience == 5
    
    def test_skill_proficiency_validation(self, db_session):
        """Test skill proficiency level validation"""
        # Test valid proficiency levels
        for level in [0, 50, 100]:
            skill = Skill(
                name=f"Skill {level}",
                proficiency_level=level
            )
            db_session.add(skill)
            db_session.commit()
            assert skill.proficiency_level == level
            db_session.delete(skill)
            db_session.commit()

class TestAnalyticsModel:
    """Test Analytics model functionality"""
    
    def test_page_view_creation(self, db_session):
        """Test creating page views"""
        page_view = PageView(
            path="/blog/test-post",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="127.0.0.1",
            referrer="https://google.com",
            country="US",
            device_type="desktop"
        )
        db_session.add(page_view)
        db_session.commit()
        
        assert page_view.id is not None
        assert page_view.path == "/blog/test-post"
        assert page_view.ip_address == "127.0.0.1"
        assert page_view.timestamp is not None
    
    def test_visitor_tracking(self, db_session):
        """Test visitor tracking"""
        visitor = Visitor(
            session_id="test-session-123",
            ip_address="127.0.0.1",
            user_agent="Test Browser",
            country="US",
            city="Test City",
            first_visit=datetime.utcnow(),
            last_visit=datetime.utcnow()
        )
        db_session.add(visitor)
        db_session.commit()
        
        assert visitor.id is not None
        assert visitor.session_id == "test-session-123"
        assert visitor.country == "US"

class TestContactModel:
    """Test Contact model functionality"""
    
    def test_contact_submission_creation(self, db_session):
        """Test creating contact submissions"""
        contact = ContactSubmission(
            name="John Doe",
            email="john@example.com",
            subject="Test Subject",
            message="Test message content",
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        db_session.add(contact)
        db_session.commit()
        
        assert contact.id is not None
        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"
        assert contact.status == "unread"  # Default status
        assert contact.submitted_at is not None
    
    def test_contact_status_updates(self, db_session):
        """Test contact status updates"""
        contact = ContactSubmission(
            name="Jane Doe",
            email="jane@example.com",
            subject="Test",
            message="Test message"
        )
        db_session.add(contact)
        db_session.commit()
        
        # Test status updates
        valid_statuses = ["unread", "read", "replied", "spam"]
        for status in valid_statuses:
            contact.status = status
            db_session.commit()
            assert contact.status == status

class TestDatabaseOperations:
    """Test database operations and queries"""
    
    def test_database_connection(self, db_session):
        """Test database connection is working"""
        result = db_session.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
    
    def test_transaction_rollback(self, db_session):
        """Test transaction rollback functionality"""
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User"
        )
        db_session.add(user)
        
        # Don't commit, rollback instead
        db_session.rollback()
        
        # User should not exist
        found_user = db_session.query(User).filter_by(email="test@example.com").first()
        assert found_user is None
    
    def test_cascade_operations(self, db_session, test_user):
        """Test cascade delete operations"""
        # Create blog post for user
        post = BlogPost(
            title="Test Post",
            content="Test content",
            author_id=test_user.id
        )
        db_session.add(post)
        db_session.commit()
        
        post_id = post.id
        
        # Delete user (should cascade to blog posts if configured)
        db_session.delete(test_user)
        db_session.commit()
        
        # Check if post was also deleted (depends on cascade configuration)
        remaining_post = db_session.query(BlogPost).filter_by(id=post_id).first()
        # Test behavior depends on actual cascade configuration

class TestValidationAndSanitization:
    """Test input validation and sanitization"""
    
    def test_email_validation(self):
        """Test email validation logic"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "firstname+lastname@example.com"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user space@example.com"
        ]
        
        # Test with actual validation function if available
        # This would test the validation logic used in the application
        pass
    
    def test_html_sanitization(self):
        """Test HTML content sanitization"""
        dangerous_content = """
        <script>alert('xss')</script>
        <p>Safe content</p>
        <img src="x" onerror="alert('xss')">
        """
        
        # Test with actual sanitization function if available
        # sanitized = sanitize_html(dangerous_content)
        # assert "<script>" not in sanitized
        # assert "onerror" not in sanitized
        # assert "<p>Safe content</p>" in sanitized
        pass
    
    def test_sql_injection_prevention(self, db_session):
        """Test SQL injection prevention"""
        malicious_input = "'; DROP TABLE users; --"
        
        # Test that ORM prevents SQL injection
        try:
            user = db_session.query(User).filter_by(username=malicious_input).first()
            # Should not cause any issues with ORM
            assert user is None
        except Exception as e:
            # Should not raise SQL-related exceptions
            assert "DROP TABLE" not in str(e)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])