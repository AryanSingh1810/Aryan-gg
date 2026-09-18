from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.song import Song
from models.room import Room, GameScore

__all__ = ["db", "User", "Song", "Room", "GameScore"]
