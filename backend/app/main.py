from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.logger import logger
from app.api.chat import router as chat_router
from app.api.disease import router as disease_router
from app.api.report import router as report_router
from app.api.auth import router as auth_router
from app.api.deps import get_current_user
from app.core.database import engine, Base
from app.core.limiter import limiter
from app.models.session import UserSession # Import models to register them
import os

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

is_prod = os.getenv("BUILD") == "production"

app = FastAPI(
    title="GH Backend",
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json"
)

# Rate limiting configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.on_event("startup")
async def startup():
    # Create tables in the database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
# This allows the frontend to access images saved in the uploads folder
uploads_dir = os.getenv("UPLOAD_DIR", "uploads")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app.mount("/api/static", StaticFiles(directory=uploads_dir), name="static")

# Public Routes
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Protected Routes
app.include_router(chat_router, prefix="/api", tags=["chat"], dependencies=[Depends(get_current_user)])
app.include_router(disease_router, prefix="/api", tags=["disease"], dependencies=[Depends(get_current_user)])
app.include_router(report_router, prefix="/api/report", tags=["report"], dependencies=[Depends(get_current_user)])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
