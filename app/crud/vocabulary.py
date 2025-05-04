from typing import Optional, List
from sqlmodel import Session, select
from app.models.vocabulary import Vocabulary

def list_for_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Vocabulary]:
    """Get vocabulary items for a specific user with pagination"""
    return db.exec(select(Vocabulary).where(Vocabulary.user_id == user_id).offset(skip).limit(limit)).all()

def add(db: Session, user_id: int, *, word: str, meaning: str, example: Optional[str] = None):
    vocab = Vocabulary(user_id=user_id, word=word, meaning=meaning, example=example)
    db.add(vocab); db.commit(); db.refresh(vocab)
    return vocab

def delete(db: Session, user_id: int, vocab_id: int):
    vocab = db.get(Vocabulary, vocab_id)
    if not vocab or vocab.user_id != user_id:
        return False
    db.delete(vocab); db.commit()
    return True
