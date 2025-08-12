"""
User Authentication Service
Handles user registration, login, JWT tokens, and session management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..models.db_models import User
from ..core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    def __init__(self):
        """Initialize authentication service"""
        self.pwd_context = pwd_context
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username/email and password"""
        user = self.get_user_by_username_or_email(db, username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def get_user_by_username_or_email(self, db: Session, identifier: str) -> Optional[User]:
        """Get user by username or email"""
        user = db.query(User).filter(User.username == identifier).first()
        if not user:
            user = db.query(User).filter(User.email == identifier).first()
        return user
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, db: Session, username: str, email: str, password: str, 
                   full_name: str = None, github_username: str = None) -> User:
        """Create a new user"""
        
        # Check if user already exists
        if self.get_user_by_username_or_email(db, username):
            raise ValueError("Username already exists")
        if self.get_user_by_username_or_email(db, email):
            raise ValueError("Email already exists")
        
        # Create new user
        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            github_username=github_username,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ Created new user: {username}")
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return {"username": username, "exp": payload.get("exp")}
        except JWTError:
            return None
    
    def get_current_user(self, db: Session, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        username = payload.get("username")
        if username is None:
            return None
        
        user = self.get_user_by_username_or_email(db, username)
        return user if user and user.is_active else None
    
    def update_user_profile(self, db: Session, user_id: int, updates: Dict[str, Any]) -> Optional[User]:
        """Update user profile"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        # Update allowed fields
        allowed_fields = ['full_name', 'github_username', 'linkedin_profile', 'skills', 'bio']
        for field, value in updates.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ Updated profile for user: {user.username}")
        return user
    
    def change_password(self, db: Session, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # Verify old password
        if not self.verify_password(old_password, user.hashed_password):
            return False
        
        # Update password
        user.hashed_password = self.get_password_hash(new_password)
        db.commit()
        
        logger.info(f"✅ Password changed for user: {user.username}")
        return True
    
    def deactivate_user(self, db: Session, user_id: int) -> bool:
        """Deactivate a user account"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_active = False
        db.commit()
        
        logger.info(f"✅ Deactivated user: {user.username}")
        return True
    
    def get_user_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return {}
        
        from ..models.db_models import ProblemClaim, Solution
        
        # Get user statistics
        claimed_problems = db.query(ProblemClaim).filter(ProblemClaim.user_id == user_id).count()
        completed_solutions = db.query(Solution).filter(
            Solution.contributor_id == user_id,
            Solution.status == "completed"
        ).count()
        in_progress_solutions = db.query(Solution).filter(
            Solution.contributor_id == user_id,
            Solution.status == "in_development"
        ).count()
        
        return {
            "username": user.username,
            "member_since": user.created_at.strftime("%Y-%m-%d"),
            "claimed_problems": claimed_problems,
            "completed_solutions": completed_solutions,
            "in_progress_solutions": in_progress_solutions,
            "github_username": user.github_username,
            "skills": user.skills or [],
            "bio": user.bio
        }

# Global instance
auth_service = AuthService()
