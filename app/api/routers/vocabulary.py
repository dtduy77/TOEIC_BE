from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlmodel import Session, select
from typing import List, Optional
import logging
from app.api.deps import get_current_user, security
from app.db.session import get_session
from app.schemas import vocabulary as schema_vocab
from app.crud import vocabulary as crud_vocab
from app.models.vocabulary import Vocabulary
from firebase_admin import auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])

@router.get("/", response_model=List[schema_vocab.VocabOut])
def list_vocab(db: Session = Depends(get_session), current = Depends(get_current_user)):
    return crud_vocab.list_for_user(db, current.id)

@router.get("/user", response_model=List[schema_vocab.VocabOut])
async def get_user_vocabulary(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_session)
):
    """Get vocabulary items for the current user with pagination"""
    try:
        # Get the token from the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token format")

        token = auth_header.split("Bearer ")[1]
        
        # Verify the Firebase token
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")
            
            # Try to get user by email
            from app.crud import user as crud_user
            user = crud_user.get_by_email(db, email)
            
            if user is None:
                # Create a temporary user if not found
                from app.models.user import User
                user = User(
                    id=1,  # Temporary ID for demo purposes
                    email=email,
                    username=email,
                    full_name=email.split('@')[0],
                    hashed_pw="firebase_auth"
                )
                
                # Try to create the user in the database
                try:
                    user = crud_user.create_without_firebase_uid(db, 
                                                          username=email,
                                                          email=email,
                                                          full_name=email.split('@')[0],
                                                          hashed_pw="firebase_auth")
                except Exception as create_error:
                    logger.error(f"Error creating user: {str(create_error)}")
                    # Continue with temporary user
                    pass
            
            # Try to get the user's vocabulary items
            try:
                # If we have a valid user ID, use it to fetch vocabulary items
                if user and user.id:
                    return crud_vocab.list_for_user(db, user.id, skip=skip, limit=limit)
                else:
                    # Try to get all vocabulary items (for testing/demo purposes)
                    # In a production environment, you would want to restrict this
                    all_vocab = db.exec(select(Vocabulary)).all()
                    logger.info(f"Found {len(all_vocab)} vocabulary items in total")
                    return all_vocab
            except Exception as vocab_error:
                logger.error(f"Error fetching vocabulary: {str(vocab_error)}")
                # Return empty list as fallback
                return []
            
        except Exception as token_error:
            logger.error(f"Token verification error: {str(token_error)}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
            
    except Exception as e:
        logger.error(f"Error in get_user_vocabulary: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")

@router.post("/", response_model=schema_vocab.VocabOut, status_code=201)
def add_vocab(data: schema_vocab.VocabIn,
              db=Depends(get_session), current=Depends(get_current_user)):
    return crud_vocab.add(db, current.id, **data.dict())

@router.delete("/{vocab_id}", status_code=204)
def delete_vocab(vocab_id: int,
                 db=Depends(get_session), current=Depends(get_current_user)):
    if not crud_vocab.delete(db, current.id, vocab_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Word not found")
