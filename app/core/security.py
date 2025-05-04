from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import get_settings
from typing import Optional

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_ctx.verify(password, hashed)

def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    to_encode = {"sub": subject, "exp": datetime.utcnow() +
                 timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials")
