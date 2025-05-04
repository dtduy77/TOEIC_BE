from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import random

from ..database import crud, models, schemas
from ..database.database import get_db
from .users import get_current_active_user

router = APIRouter(
    prefix="/vocabulary",
    tags=["vocabulary"],
    responses={404: {"description": "Not found"}},
)

# Public vocabulary endpoints
@router.get("/", response_model=List[schemas.Vocabulary])
def get_all_vocabularies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    vocabularies = crud.get_vocabularies(db, skip=skip, limit=limit)
    return vocabularies

@router.get("/{vocabulary_id}", response_model=schemas.Vocabulary)
def get_vocabulary(vocabulary_id: int, db: Session = Depends(get_db)):
    db_vocabulary = crud.get_vocabulary(db, vocabulary_id=vocabulary_id)
    if db_vocabulary is None:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    return db_vocabulary

@router.post("/", response_model=schemas.Vocabulary)
def create_vocabulary(
    vocabulary: schemas.VocabularyCreate, 
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    # Check if the word already exists
    db_vocabulary = crud.get_vocabulary_by_word(db, word=vocabulary.word)
    if db_vocabulary:
        raise HTTPException(status_code=400, detail="Word already exists")
    
    # Create the vocabulary
    return crud.create_vocabulary(db=db, vocabulary=vocabulary)

# User-specific vocabulary endpoints
@router.get("/user/", response_model=List[schemas.UserVocabularyDetail])
def get_user_vocabularies(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    user_vocabularies = crud.get_user_vocabularies(db, user_id=current_user.id, skip=skip, limit=limit)
    
    # Convert to response model format
    result = []
    for vocab, mastery_level, notes in user_vocabularies:
        vocab_dict = {
            "id": vocab.id,
            "word": vocab.word,
            "meaning": vocab.meaning,
            "example": vocab.example,
            "mastery_level": mastery_level,
            "notes": notes
        }
        result.append(schemas.UserVocabularyDetail(**vocab_dict))
    
    return result

@router.post("/user/add/{vocabulary_id}", response_model=schemas.UserVocabulary)
def add_vocabulary_to_user(
    vocabulary_id: int,
    mastery_level: Optional[int] = 0,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    # Check if vocabulary exists
    db_vocabulary = crud.get_vocabulary(db, vocabulary_id=vocabulary_id)
    if db_vocabulary is None:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    
    # Add vocabulary to user
    return crud.add_vocabulary_to_user(
        db=db, 
        user_id=current_user.id, 
        vocabulary_id=vocabulary_id,
        mastery_level=mastery_level,
        notes=notes
    )

@router.put("/user/update/{vocabulary_id}", response_model=schemas.UserVocabulary)
def update_user_vocabulary(
    vocabulary_id: int,
    mastery_level: Optional[int] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    # Update user vocabulary
    db_user_vocabulary = crud.update_user_vocabulary(
        db=db, 
        user_id=current_user.id, 
        vocabulary_id=vocabulary_id,
        mastery_level=mastery_level,
        notes=notes
    )
    
    if db_user_vocabulary is None:
        raise HTTPException(status_code=404, detail="Vocabulary not in user's list")
    
    return db_user_vocabulary

@router.delete("/user/remove/{vocabulary_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_vocabulary_from_user(
    vocabulary_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    # Remove vocabulary from user
    success = crud.remove_vocabulary_from_user(
        db=db, 
        user_id=current_user.id, 
        vocabulary_id=vocabulary_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Vocabulary not in user's list")
    
    return {"detail": "Vocabulary removed from user's list"}

# Quiz generation with user's vocabulary
@router.get("/quiz/user/", response_model=List[schemas.QuizQuestion])
def generate_user_quiz(
    num_questions: int = 10,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    # Get user's vocabularies
    user_vocabularies = crud.get_user_random_vocabularies(db, user_id=current_user.id, count=num_questions)
    
    if len(user_vocabularies) < num_questions:
        raise HTTPException(
            status_code=400, 
            detail=f"Not enough vocabulary words in your list. You have {len(user_vocabularies)} words, but requested {num_questions} questions."
        )
    
    # Get all vocabularies for wrong choices
    all_vocabularies = crud.get_vocabularies(db)
    
    # Generate quiz questions
    questions = []
    for vocab in user_vocabularies:
        choices = [vocab.meaning]
        # Generate 3 wrong choices
        wrong_choices = random.sample([v.meaning for v in all_vocabularies if v.id != vocab.id], 3)
        choices.extend(wrong_choices)
        random.shuffle(choices)
        
        questions.append(schemas.QuizQuestion(
            question=f"What is the meaning of '{vocab.word}'?",
            choices=choices,
            answer=vocab.meaning
        ))
    
    return questions
