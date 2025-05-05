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

# Removed the QuizType enum as we're letting users choose number of questions directly

class QuizQuestion(BaseModel):
    question     : str  # We'll format this as "What is the meaning of 'word'?"
    answer       : str  # The correct answer
    choices      : list[str]  # All possible choices including the correct answer

class QuizResponse(BaseModel):
    questions: list[QuizQuestion]
    total_vocabulary: int

@router.get("/generate/", response_model=QuizResponse)
def generate(
    num_questions: int = Query(10, description="Number of questions for the quiz (default: 10)"),
    db: Session = Depends(get_session),
    current = Depends(get_current_user)
):
    try:
        # Using the num_questions parameter directly
        
        # Get user's vocabulary
        vocab = crud_vocab.list_for_user(db, current.id)
        
        # Check if user has enough vocabulary for the requested quiz
        if len(vocab) < 2:
            raise HTTPException(400, "Need at least 2 words in your vocabulary to generate a quiz")
        
        # Get the total vocabulary count for the user
        total_vocabulary = len(vocab)

        # If we have fewer words than requested, adjust the number of questions
        if total_vocabulary < num_questions:
            logger.warning(f"User {current.id} has only {total_vocabulary} words but requested {num_questions} questions - adjusting quiz size")
            num_questions = total_vocabulary

        # If we have fewer than 2 words, we can't create a quiz
        if total_vocabulary < 2:
            return QuizResponse(questions=[], total_vocabulary=total_vocabulary)
        
        # Randomly select vocabulary for the quiz
        quiz_vocabulary = sample(vocab, num_questions)
        
        # Create quiz questions
        quiz_questions = []
        
        for item in quiz_vocabulary:
            # Format the question
            question = f"What is the meaning of '{item.word}'?"
            
            # The correct answer is the Vietnamese translation
            answer = item.meaning
            
            # Get distractors (incorrect answers) from other vocabulary
            # We need to make sure we don't include the correct answer
            other_vocab = [v for v in vocab if v.id != item.id]
            
            # If we have fewer than 3 other vocabulary items, we'll have fewer distractors
            num_distractors = min(3, len(other_vocab))
            
            if num_distractors > 0:
                distractors = sample([v.meaning for v in other_vocab], num_distractors)
            else:
                distractors = []
                
            # Combine correct answer and distractors, then shuffle
            choices = [answer] + distractors
            shuffle(choices)
            
            # Create the quiz question
            quiz_questions.append(QuizQuestion(
                question=question,
                answer=answer,
                choices=choices
            ))
        
        logger.info(f"Generated {len(quiz_questions)} quiz questions for user {current.id}")
        return QuizResponse(questions=quiz_questions, total_vocabulary=total_vocabulary)
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(500, f"Error generating quiz: {str(e)}")
