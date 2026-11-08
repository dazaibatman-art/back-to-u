import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if present
load_dotenv(BASE_DIR / ".env")


def get_database_uri() -> str:
    """Resolve database URI reliably using absolute paths for local SQLite."""
    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        db_path = (BASE_DIR / "instance" / "lost_and_found.db").resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.as_posix()}"
    
    # If it's a relative SQLite URI, resolve it against BASE_DIR
    if raw_url.startswith("sqlite:///") and not raw_url.startswith("sqlite:////"):
        rel_path = raw_url.replace("sqlite:///", "")
        if rel_path != ":memory:" and not Path(rel_path).is_absolute():
            abs_path = (BASE_DIR / rel_path).resolve()
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{abs_path.as_posix()}"
            
    return raw_url


def get_upload_folder() -> str:
    """Resolve upload folder reliably as absolute path."""
    raw_folder = os.environ.get("UPLOAD_FOLDER", "uploads")
    p = Path(raw_folder)
    if not p.is_absolute():
        p = (BASE_DIR / p).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-group-no1-change-in-production")
    
    # Database
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = get_upload_folder()
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB max request
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_IMAGE_FILE_SIZE = 5 * 1024 * 1024  # 5 MB per image

    # Security & Sessions
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 14  # 14 days
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per day; 60 per hour")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_STRATEGY = "fixed-window"

    # Branding
    APP_NAME = "Group No1"
    APP_TYPE = "Global Lost & Found Management System"
    APP_TAGLINE = "Lost Something? Found Something? Let's Bring It Back."
    APP_PAGE_TITLE = "Group No1 — Global Lost & Found"
    APP_FOOTER = "© Group No1 | Global Lost & Found Management System"


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration with separate in-memory SQLite and StaticPool."""
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False}
    }
    UPLOAD_FOLDER = str(BASE_DIR / "tests" / "test_uploads")
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
