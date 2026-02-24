from typing import Annotated, Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings

security = HTTPBearer()

async def get_current_user(token: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    """
    Dependency to get the current authenticated user from the Authorization header.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    access_token = token.credentials

    if not access_token:
        print("DEBUG: No access_token found in header.")
        raise credentials_exception

    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            print("DEBUG: No username in token payload.")
            raise credentials_exception
        
        # Verify user exists in our fixed list
        if username not in settings.FIXED_USERS:
             print(f"DEBUG: Username '{username}' not found in FIXED_USERS.")
             raise credentials_exception
             
        return username
        
    except jwt.PyJWTError as e:
        print(f"DEBUG: JWT Decode Error: {e}")
        raise credentials_exception
