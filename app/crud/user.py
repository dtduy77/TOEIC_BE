from typing import Optional, Dict, Any
from sqlmodel import Session, select
from app.models.user import User
from app.core.security import hash_password, verify_password
import logging

logger = logging.getLogger(__name__)

def get_by_username(db: Session, username: str) -> Optional[User]:
    return db.exec(select(User).where(User.username == username)).first()

def get_by_email(db: Session, email: str) -> Optional[User]:
    try:
        return db.exec(select(User).where(User.email == email)).first()
    except Exception as e:
        logger.error(f"Error getting user by email: {str(e)}")
        return None

def get_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[User]:
    try:
        return db.exec(select(User).where(User.firebase_uid == firebase_uid)).first()
    except Exception as e:
        logger.error(f"Error getting user by firebase_uid: {str(e)}")
        return None

def create(db: Session, *, username: str, password: str, email: str, full_name: str, firebase_uid: str = None) -> User:
    try:
        user = User(username=username,
                    email=email,
                    full_name=full_name,
                    hashed_pw=hash_password(password),
                    firebase_uid=firebase_uid)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise

def create_without_firebase_uid(db: Session, **user_data: Dict[str, Any]) -> User:
    """Create a user without the firebase_uid field to handle database schema issues"""
    try:
        # Create a user with only the fields we know exist in the database
        user = User(
            username=user_data.get("username"),
            email=user_data.get("email"),
            full_name=user_data.get("full_name"),
            hashed_pw=user_data.get("hashed_pw")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error creating user without firebase_uid: {str(e)}")
        db.rollback()
        raise

def authenticate(db: Session, username: str, password: str) -> Optional[User]:
    user = get_by_username(db, username)
    if user and verify_password(password, user.hashed_pw):
        return user
    return None
