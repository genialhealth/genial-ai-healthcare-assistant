from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import jwt
from app.core.config import settings
from app.core.hashing import pwd_context

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a bcrypt hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Generates a bcrypt hash from a plain password.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
