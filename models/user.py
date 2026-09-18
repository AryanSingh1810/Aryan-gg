from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(100), default="avatar-1")
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)
    best_score = db.Column(db.Integer, default=0)
    favorite_category = db.Column(db.String(50), default="English")
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        avg_score = round(self.total_points / self.games_played, 1) if self.games_played > 0 else 0
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "avatar": self.avatar,
            "games_played": self.games_played,
            "games_won": self.games_won,
            "total_points": self.total_points,
            "best_score": self.best_score,
            "average_score": avg_score,
            "favorite_category": self.favorite_category,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
