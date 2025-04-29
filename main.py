# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import random
import uvicorn

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vocabulary dataset
class Vocabulary(BaseModel):
    word: str
    meaning: str
    example: str

# Mock database
vocab_list = [
    Vocabulary(word="abandon", meaning="to leave behind", example="The crew abandoned the sinking ship."),
    Vocabulary(word="beneficial", meaning="helpful", example="Reading is beneficial to your mind."),
    Vocabulary(word="candidate", meaning="a person who applies for a job", example="She was a strong candidate for the role."),
    # ✅ Add more words here
]

class QuizQuestion(BaseModel):
    question: str
    choices: List[str]
    answer: str

@app.get("/flashcards/", response_model=List[Vocabulary])
def get_flashcards():
    return vocab_list

@app.get("/quiz/generate/", response_model=List[QuizQuestion])
def generate_quiz(num_questions: int = 15):
    if num_questions > len(vocab_list):
        raise HTTPException(status_code=400, detail="Not enough vocabulary words.")

    selected = random.sample(vocab_list, num_questions)
    questions = []

    for vocab in selected:
        choices = [vocab.meaning]
        # Generate 3 wrong choices
        wrong_choices = random.sample([v.meaning for v in vocab_list if v.word != vocab.word], 3)
        choices.extend(wrong_choices)
        random.shuffle(choices)
        questions.append(QuizQuestion(
            question=f"What is the meaning of '{vocab.word}'?",
            choices=choices,
            answer=vocab.meaning
        ))
    return questions

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)