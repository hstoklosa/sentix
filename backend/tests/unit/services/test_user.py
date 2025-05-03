import pytest
from sqlmodel import Session
from app.services.user import (
    create_user, 
    get_user_by_email, 
    get_user_by_username, 
    get_user_by_id, 
    authenticate_user
)
from app.schemas.user import UserCreate
from app.core.security import verify_password

class TestUserService:
    """Unit tests for the user service module"""
    
    def test_create_user(self, db_session: Session, user_factory):
        """Test user creation with valid data"""
        # Arrange
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
            is_superuser=False
        )
        
        # Act
        created_user = create_user(
            session=db_session,
            user=user_data
        )
        
        # Assert
        assert created_user.id is not None
        assert created_user.username == user_data.username
        assert created_user.email == user_data.email
        assert created_user.is_superuser == user_data.is_superuser
        assert verify_password(user_data.password, created_user.password)
        
    def test_get_user_by_email(self, db_session: Session, user_factory):
        """Test retrieving a user by email"""
        # Arrange
        user_data = user_factory(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
        )
        create_user(session=db_session, user=user_data)
        
        # Act
        user = get_user_by_email(
            session=db_session,
            email=user_data.email
        )
        
        # Assert
        assert user is not None
        assert user.email == user_data.email
        
    def test_get_user_by_email_nonexistent(self, db_session: Session):
        """Test retrieving a nonexistent user by email returns None"""
        # Act
        user = get_user_by_email(
            session=db_session,
            email="nonexistent@example.com"
        )
        
        # Assert
        assert user is None
        
    def test_get_user_by_username(self, db_session: Session, user_factory):
        """Test retrieving a user by username"""
        # Arrange
        user_data = user_factory(
            username="testuser", 
            email="test@example.com",
            password="TestPassword123!"
        )
        create_user(session=db_session, user=user_data)
        
        # Act
        user = get_user_by_username(
            session=db_session,
            username=user_data.username
        )
        
        # Assert
        assert user is not None
        assert user.username == user_data.username
        
    def test_get_user_by_username_nonexistent(self, db_session: Session):
        """Test retrieving a nonexistent user by username returns None"""
        # Act
        user = get_user_by_username(
            session=db_session,
            username="nonexistent"
        )
        
        # Assert
        assert user is None
        
    def test_get_user_by_id(self, db_session: Session, user_factory):
        """Test retrieving a user by ID"""
        # Arrange
        user_data = user_factory(
            username="testuser", 
            email="test@example.com",
            password="TestPassword123!"
        )
        created_user = create_user(session=db_session, user=user_data)
        
        # Act
        user = get_user_by_id(
            session=db_session,
            user_id=created_user.id
        )
        
        # Assert
        assert user is not None
        assert user.id == created_user.id
        
    def test_get_user_by_id_nonexistent(self, db_session: Session):
        """Test retrieving a nonexistent user by ID returns None"""
        # Act
        user = get_user_by_id(
            session=db_session,
            user_id=9999
        )
        
        # Assert
        assert user is None
        
    def test_authenticate_user_with_email(self, db_session: Session, user_factory):
        """Test authenticating a user with email and password"""
        # Arrange
        password = "TestPassword123!"
        user_data = user_factory(
            username="testuser", 
            email="test@example.com",
            password=password
        )
        create_user(session=db_session, user=user_data)
        
        # Act
        user = authenticate_user(
            session=db_session,
            email=user_data.email,
            password=password
        )
        
        # Assert
        assert user is not None
        assert user.email == user_data.email
        
    def test_authenticate_user_with_username(self, db_session: Session, user_factory):
        """Test authenticating a user with username and password"""
        # Arrange
        password = "TestPassword123!"
        user_data = user_factory(
            username="testuser", 
            email="test@example.com",
            password=password
        )
        create_user(session=db_session, user=user_data)
        
        # Act
        user = authenticate_user(
            session=db_session,
            username=user_data.username,
            password=password
        )
        
        # Assert
        assert user is not None
        assert user.username == user_data.username
        
    def test_authenticate_user_invalid_email(self, db_session: Session):
        """Test authentication with invalid email returns None"""
        # Act
        user = authenticate_user(
            session=db_session,
            email="nonexistent@example.com",
            password="TestPassword123!"
        )
        
        # Assert
        assert user is None
        
    def test_authenticate_user_invalid_username(self, db_session: Session):
        """Test authentication with invalid username returns None"""
        # Act
        user = authenticate_user(
            session=db_session,
            username="nonexistent",
            password="TestPassword123!"
        )
        
        # Assert
        assert user is None
        
    def test_authenticate_user_invalid_password(self, db_session: Session, user_factory):
        """Test authentication with invalid password returns None"""
        # Arrange
        user_data = user_factory(
            username="testuser", 
            email="test@example.com",
            password="TestPassword123!"
        )
        create_user(session=db_session, user=user_data)
        
        # Act
        user = authenticate_user(
            session=db_session,
            email=user_data.email,
            password="WrongPassword123!"
        )
        
        # Assert
        assert user is None 