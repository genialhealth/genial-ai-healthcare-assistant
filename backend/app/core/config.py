from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.hashing import pwd_context

class Settings(BaseSettings):
    """
    Application settings and environment variables.
    
    Values are automatically loaded from the system environment or a .env file.
    """
    
    # API Configs
    MEDGEMMA_27_API_KEY: str = Field(description="API Key for the MedGemma 27B model provider.")
    MEDGEMMA_4_API_KEY: str = Field(description="API Key for the MedGemma 4B model provider.")
    MEDGEMMA_27_URL: str = Field(description="Base URL for the MedGemma 27B model API.")
    MEDGEMMA_4_URL: str = Field(description="Base URL for the MedGemma 4B model API.")
    MEDGEMMA_27_NAME: str = Field(description="Model identifier name for MedGemma 27B.")
    MEDGEMMA_4_NAME: str = Field(description="Model identifier name for MedGemma 4B.")
    
    MEDAI_URL: str = Field(description="Internal URL for the Genial Team AI classification microservice.")

    GEMINI_API_KEY: str = Field(description="API Key for Google Gemini services.")
    GEMINI_BASE_URL: str = Field(description="Base URL for Gemini API.")
    GEMINI_MODEL: str = Field(description="The specific Gemini model identifier to use.")

    # Auth Configs
    SECRET_KEY: str = Field(
        default="09d25e094faa6cp2556c818168b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="Key used for signing JWT tokens."
    )
    ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=43200, 
        description="Token expiration time in minutes (default is 30 days)."
    )
    
    # Fixed Users (username: hashed_password)
    FIXED_USERS: dict[str, str] = {
        "admin": pwd_context.hash("admin"),
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
