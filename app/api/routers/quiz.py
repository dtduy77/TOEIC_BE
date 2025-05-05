from random import sample, shuffle
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_user
from sqlmodel import Session
from app.db.session import get_session
from app.crud import vocabulary as crud_vocab
from pydantic import BaseModel
from enum import Enum
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quiz", tags=["quiz"])

class QuizType(str, Enum):
    SHORT = "short"
    LONG = "long"

class QuizQuestion(BaseModel):
    question     : str  # We'll format this as "What is the meaning of 'word'?"
    answer       : str  # The correct answer
    choices      : list[str]  # All possible choices including the correct answer

@router.get("/generate/", response_model=list[QuizQuestion])
def generate(
    quiz_type: QuizType = Query(None, description="Type of quiz: short (20 questions) or long (60 questions)"),
    num_questions: int = Query(15, description="Custom number of questions (overrides quiz_type if provided)"),
    db: Session = Depends(get_session),
    current = Depends(get_current_user)
):
    try:
        # Determine the number of questions based on quiz_type or custom num_questions
        if quiz_type and not num_questions:
            if quiz_type == QuizType.SHORT:
                num_questions = 20
            elif quiz_type == QuizType.LONG:
                num_questions = 60
        
        # Get user's vocabulary
        vocab = crud_vocab.list_for_user(db, current.id)
        
        # Check if user has enough vocabulary for the requested quiz
        if len(vocab) < 4:
            raise HTTPException(400, "Need at least 4 words in your vocabulary to generate a quiz")
        
        # Check if user has enough vocabulary for the requested number of questions
        # We need at least num_questions + 3 words (for distractors)
        if len(vocab) < num_questions:
            raise HTTPException(400, f"Not enough vocabulary words. You have {len(vocab)} words but need at least {num_questions} for this quiz type.")

        # Select random vocabulary items for the quiz
        chosen = sample(vocab, min(num_questions, len(vocab)))
        
        # Generate quiz questions
        out: list[QuizQuestion] = []
        for item in chosen:
            # Get distractors (wrong answers) from other vocabulary items
            distractors = sample([v.meaning for v in vocab if v.id != item.id], min(3, len(vocab)-1))
            opts = [item.meaning, *distractors]
            shuffle(opts)  # Randomize the order of options
            
            # Create quiz question with the expected field names
            out.append(QuizQuestion(
                question=f"What is the meaning of '{item.word}'?",
                answer=item.meaning,
                choices=opts
            ))
        
        logger.info(f"Generated {len(out)} quiz questions for user {current.id}")
        return out
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(500, f"Error generating quiz: {str(e)}")
