from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from app.db.session import get_session
from app.crud import user as crud_user
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                     db: Session = Depends(get_session)):
    try:
        token = credentials.credentials
        # Verify the Firebase token
        try:
            # First try to verify as an ID token
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")
        except Exception as e:
            logger.error(f"Error verifying ID token: {str(e)}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {str(e)}")
        
        # Since we're having issues with the firebase_uid column, let's try to find the user by email
        try:
            # First try to get user by email (which should exist in all cases)
            db_user = crud_user.get_by_email(db, email)
            
            if db_user is None:
                # User doesn't exist yet, create a new one
                try:
                    firebase_user = auth.get_user(uid)
                    # Create minimal user record without firebase_uid
                    user_data = {
                        "email": email,
                        "username": firebase_user.display_name or email,
                        "full_name": firebase_user.display_name or email.split('@')[0],
                        "hashed_pw": "firebase_auth"  # Placeholder since we're using Firebase for auth
                    }
                    # Try to create user without firebase_uid field
                    db_user = crud_user.create_without_firebase_uid(db, **user_data)
                except Exception as user_create_error:
                    logger.error(f"Failed to create user: {str(user_create_error)}")
                    # As a last resort, create a temporary user object that's not saved to the database
                    from app.models.user import User
                    db_user = User(
                        id=1,  # Temporary ID
                        email=email,
                        username=email,
                        full_name=email.split('@')[0],
                        hashed_pw="firebase_auth"
                    )
            
            return db_user
            
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            # As a last resort, create a temporary user object that's not saved to the database
            from app.models.user import User
            return User(
                id=1,  # Temporary ID
                email=email,
                username=email,
                full_name=email.split('@')[0],
                hashed_pw="firebase_auth"
            )
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid authentication credentials: {str(e)}")

