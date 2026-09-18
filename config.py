import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
raw_db_url = os.getenv("DATABASE_URL")
if raw_db_url and raw_db_url.startswith("sqlite:///") and not (len(raw_db_url) > 11 and raw_db_url[10] == ":"):
    rel_path = raw_db_url[len("sqlite:///"):]
    target_path = (BASE_DIR / rel_path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    RESOLVED_DB_PATH = f"sqlite:///{target_path.as_posix()}"
elif raw_db_url:
    RESOLVED_DB_PATH = raw_db_url
else:
    RESOLVED_DB_PATH = f"sqlite:///{ (DB_DIR / 'database.db').as_posix() }"

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "draw_the_song_super_secret_music_key_2026")
    SQLALCHEMY_DATABASE_URI = RESOLVED_DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    APP_NAME = "DRAW & GUESS"
    APP_TAGLINE = "Draw it. Guess it. Win it."
    APP_SHORT_NAME = "D&G"

    # Game Defaults & Limits
    MIN_PLAYERS = 2
    MAX_PLAYERS = 8
    MIN_ROUNDS = 3
    MAX_ROUNDS = 10
    DEFAULT_ROUNDS = 5
    MIN_ROUND_DURATION = 30
    MAX_ROUND_DURATION = 90
    DEFAULT_ROUND_DURATION = 60

    # Game Modes & Extensible Content Architecture
    GAME_MODES = {
        "song": {
            "id": "song",
            "name": "Guess the Song",
            "tagline": "Draw the clues. Guess the song.",
            "icon": "🎵",
            "categories": ["English", "Hollywood", "Trending"],
            "difficulties": ["Easy", "Medium", "Hard"],
            "badge": "Music Arena",
            "description": "Listen with your eyes! Sketch album art, iconic lyrics, instruments, and visual metaphors to get your friends to guess the hit track."
        },
        "movie": {
            "id": "movie",
            "name": "Guess the Movie",
            "tagline": "Draw the scene. Guess the movie.",
            "icon": "🎬",
            "categories": ["Hollywood", "Trending", "Popular", "Classic"],
            "difficulties": ["Easy", "Medium", "Hard"],
            "badge": "Cinema Arena",
            "description": "Become the director! Draw famous cinematic scenes, iconic movie posters, heroes, villains, and plot twists without uttering a sound."
        }
    }

    # Backward compatibility
    CATEGORIES = ["English", "Hollywood", "Trending"]

    # SocketIO
    SOCKETIO_ASYNC_MODE = "threading"
    CORS_ALLOWED_ORIGINS = "*"

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "production-must-set-this-random-string")

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
