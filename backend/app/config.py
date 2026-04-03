"""Application configuration"""
import os
from typing import List


class Settings:
    """Application settings and configuration"""
    
    # API Settings
    APP_NAME: str = "Quran Shield - Audio Analysis API"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", 
        "*"  # In production, set this to your domain
    ).split(",")
    
    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Audio Processing Settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    SUPPORTED_FORMATS: List[str] = ["mp3", "wav", "ogg", "m4a", "flac", "aac"]
    
    # Feature Extraction Settings
    SAMPLE_RATE: int = 22050  # librosa default
    N_MFCC: int = 13
    
    # Classifier Thresholds
    MUSIC_THRESHOLD: float = 0.0  # score > 0 = music
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
