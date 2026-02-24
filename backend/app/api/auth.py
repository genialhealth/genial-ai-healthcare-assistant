from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from app.schemas import UserLogin, ApiResponse, AuthResponseData
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_user
from app.core.limiter import limiter

router = APIRouter()

@router.post(
    "/login", 
    response_model=ApiResponse[AuthResponseData],
    summary="User Login",
    description="Authenticate a user with a username and password and receive a JWT access token."
)
@limiter.limit("5/minute")
async def login(request: Request, login_data: UserLogin, response: Response):
    # 1. Verify credentials
    password = settings.FIXED_USERS.get(login_data.username)
    if not password or not verify_password(login_data.password, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # 2. Create Access Token
    access_token = create_access_token(data={"sub": login_data.username})
    
    # 3. Return Token in Body (No Cookie)
    return ApiResponse(
        success=True,
        data=AuthResponseData(
            username=login_data.username, 
            message="Login successful",
            access_token=access_token
        )
    )

@router.post(
    "/logout", 
    response_model=ApiResponse[AuthResponseData],
    summary="User Logout",
    description="Logs the user out. Since we use JWT, this mainly serves as a confirmation for the client to clear their token."
)
@limiter.limit("5/minute")
async def logout(request: Request, response: Response):
    # No cookie to delete. Client handles token removal.
    return ApiResponse(
        success=True,
        data=AuthResponseData(username="", message="Logout successful")
    )

@router.get(
    "/me", 
    response_model=ApiResponse[AuthResponseData],
    summary="Get Current User",
    description="Retrieve the username of the currently authenticated user based on the JWT token."
)
@limiter.limit("20/minute")
async def read_users_me(request: Request, current_user: str = Depends(get_current_user)):
    return ApiResponse(
        success=True,
        data=AuthResponseData(username=current_user, message="Authenticated")
    )
