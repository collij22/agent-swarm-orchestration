"""
Unit tests for database models
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base
from models.user import User
from models.blog import BlogPost, BlogCategory, BlogComment
from models.portfolio import Project, Skill, Experience
from models.contact import ContactMessage
from models.analytics import PageView, VisitorSession

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestDatabaseModels:
    """Test database models"""
    
    def setup_method(self):
        """Setup test database"""
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        
    def teardown_method(self):
        """Cleanup after tests"""
        self.db.close()
        Base.metadata.drop_all(bind=engine)

class TestUserModel(TestDatabaseModels):
    """Test User model"""
    
    def test_user_creation(self):
        """Test creating a user"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_password_here"
        )
        self.db.add(user)
        self.db.commit()
        
        # Retrieve and verify
        saved_user = self.db.query(User).filter(User.username == "testuser").first()
        assert saved_user is not None
        assert saved_user.email == "test@example.com"
        assert saved_user.full_name == "Test User"
        assert saved_user.is_active is True
        assert saved_user.created_at is not None

    def test_user_unique_constraints(self):
        """Test unique constraints on username and email"""
        user1 = User(username="testuser", email="test1@example.com", hashed_password="hash1")
        user2 = User(username="testuser", email="test2@example.com", hashed_password="hash2")
        
        self.db.add(user1)
        self.db.commit()
        
        self.db.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            self.db.commit()

    def test_user_email_validation(self):
        """Test user email validation"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hash"
        )
        # Basic validation - email should contain @
        assert "@" in user.email

class TestBlogModels(TestDatabaseModels):
    """Test Blog-related models"""
    
    def test_blog_category_creation(self):
        """Test creating blog category"""
        category = BlogCategory(
            name="Technology",
            slug="technology",
            description="Tech-related posts"
        )
        self.db.add(category)
        self.db.commit()
        
        saved_category = self.db.query(BlogCategory).filter(BlogCategory.slug == "technology").first()
        assert saved_category is not None
        assert saved_category.name == "Technology"

    def test_blog_post_creation(self):
        """Test creating blog post"""
        # Create category first
        category = BlogCategory(name="Tech", slug="tech")
        self.db.add(category)
        self.db.commit()
        
        # Create user
        user = User(username="author", email="author@example.com", hashed_password="hash")
        self.db.add(user)
        self.db.commit()
        
        # Create blog post
        post = BlogPost(
            title="Test Post",
            slug="test-post",
            content="This is test content",
            excerpt="Test excerpt",
            author_id=user.id,
            category_id=category.id,
            is_published=True
        )
        self.db.add(post)
        self.db.commit()
        
        saved_post = self.db.query(BlogPost).filter(BlogPost.slug == "test-post").first()
        assert saved_post is not None
        assert saved_post.title == "Test Post"
        assert saved_post.is_published is True
        assert saved_post.view_count == 0

    def test_blog_comment_creation(self):
        """Test creating blog comment"""
        # Create necessary dependencies
        category = BlogCategory(name="Tech", slug="tech")
        user = User(username="author", email="author@example.com", hashed_password="hash")
        self.db.add_all([category, user])
        self.db.commit()
        
        post = BlogPost(
            title="Test Post",
            slug="test-post", 
            content="Content",
            author_id=user.id,
            category_id=category.id
        )
        self.db.add(post)
        self.db.commit()
        
        # Create comment
        comment = BlogComment(
            post_id=post.id,
            author_name="Commenter",
            author_email="commenter@example.com",
            content="Great post!",
            is_approved=True
        )
        self.db.add(comment)
        self.db.commit()
        
        saved_comment = self.db.query(BlogComment).filter(BlogComment.post_id == post.id).first()
        assert saved_comment is not None
        assert saved_comment.author_name == "Commenter"
        assert saved_comment.is_approved is True

class TestPortfolioModels(TestDatabaseModels):
    """Test Portfolio-related models"""
    
    def test_project_creation(self):
        """Test creating a project"""
        project = Project(
            title="Awesome Project",
            slug="awesome-project",
            description="A really awesome project",
            technologies=["Python", "FastAPI", "PostgreSQL"],
            github_url="https://github.com/user/awesome-project",
            live_url="https://awesome-project.com",
            is_featured=True
        )
        self.db.add(project)
        self.db.commit()
        
        saved_project = self.db.query(Project).filter(Project.slug == "awesome-project").first()
        assert saved_project is not None
        assert saved_project.title == "Awesome Project"
        assert saved_project.is_featured is True
        assert "Python" in saved_project.technologies

    def test_skill_creation(self):
        """Test creating a skill"""
        skill = Skill(
            name="Python",
            category="Programming Languages",
            proficiency_level=5,
            years_experience=3.5,
            is_primary=True
        )
        self.db.add(skill)
        self.db.commit()
        
        saved_skill = self.db.query(Skill).filter(Skill.name == "Python").first()
        assert saved_skill is not None
        assert saved_skill.proficiency_level == 5
        assert saved_skill.years_experience == 3.5

    def test_experience_creation(self):
        """Test creating work experience"""
        experience = Experience(
            company="Tech Corp",
            position="Senior Developer",
            description="Built awesome applications",
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31),
            technologies=["Python", "React", "AWS"],
            is_current=False
        )
        self.db.add(experience)
        self.db.commit()
        
        saved_exp = self.db.query(Experience).filter(Experience.company == "Tech Corp").first()
        assert saved_exp is not None
        assert saved_exp.position == "Senior Developer"
        assert saved_exp.is_current is False

class TestContactModel(TestDatabaseModels):
    """Test Contact model"""
    
    def test_contact_message_creation(self):
        """Test creating contact message"""
        message = ContactMessage(
            name="John Doe",
            email="john@example.com",
            subject="Inquiry",
            message="Hello, I'd like to work with you",
            is_read=False
        )
        self.db.add(message)
        self.db.commit()
        
        saved_message = self.db.query(ContactMessage).filter(ContactMessage.email == "john@example.com").first()
        assert saved_message is not None
        assert saved_message.name == "John Doe"
        assert saved_message.is_read is False

class TestAnalyticsModels(TestDatabaseModels):
    """Test Analytics models"""
    
    def test_page_view_creation(self):
        """Test creating page view record"""
        page_view = PageView(
            url="/blog/awesome-post",
            title="Awesome Post",
            referrer="https://google.com",
            user_agent="Mozilla/5.0...",
            ip_address="192.168.1.1",
            country="US",
            device_type="desktop"
        )
        self.db.add(page_view)
        self.db.commit()
        
        saved_view = self.db.query(PageView).filter(PageView.url == "/blog/awesome-post").first()
        assert saved_view is not None
        assert saved_view.country == "US"
        assert saved_view.device_type == "desktop"

    def test_visitor_session_creation(self):
        """Test creating visitor session"""
        session = VisitorSession(
            session_id="sess_123456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0...",
            country="US",
            device_type="desktop",
            pages_visited=5,
            duration_seconds=300
        )
        self.db.add(session)
        self.db.commit()
        
        saved_session = self.db.query(VisitorSession).filter(VisitorSession.session_id == "sess_123456").first()
        assert saved_session is not None
        assert saved_session.pages_visited == 5
        assert saved_session.duration_seconds == 300

class TestModelRelationships(TestDatabaseModels):
    """Test model relationships"""
    
    def test_user_blog_posts_relationship(self):
        """Test relationship between user and blog posts"""
        user = User(username="blogger", email="blogger@example.com", hashed_password="hash")
        category = BlogCategory(name="Tech", slug="tech")
        self.db.add_all([user, category])
        self.db.commit()
        
        post1 = BlogPost(title="Post 1", slug="post-1", content="Content 1", author_id=user.id, category_id=category.id)
        post2 = BlogPost(title="Post 2", slug="post-2", content="Content 2", author_id=user.id, category_id=category.id)
        self.db.add_all([post1, post2])
        self.db.commit()
        
        # Test relationship
        saved_user = self.db.query(User).filter(User.username == "blogger").first()
        assert len(saved_user.blog_posts) == 2

    def test_blog_post_comments_relationship(self):
        """Test relationship between blog post and comments"""
        user = User(username="author", email="author@example.com", hashed_password="hash")
        category = BlogCategory(name="Tech", slug="tech")
        self.db.add_all([user, category])
        self.db.commit()
        
        post = BlogPost(title="Post", slug="post", content="Content", author_id=user.id, category_id=category.id)
        self.db.add(post)
        self.db.commit()
        
        comment1 = BlogComment(post_id=post.id, author_name="User1", author_email="user1@example.com", content="Comment 1")
        comment2 = BlogComment(post_id=post.id, author_name="User2", author_email="user2@example.com", content="Comment 2")
        self.db.add_all([comment1, comment2])
        self.db.commit()
        
        # Test relationship
        saved_post = self.db.query(BlogPost).filter(BlogPost.slug == "post").first()
        assert len(saved_post.comments) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])