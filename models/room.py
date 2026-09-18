from datetime import datetime, timezone
from models import db

def utc_now():
    return datetime.now(timezone.utc)

class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    host_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    host_name = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), default="English")
    rounds = db.Column(db.Integer, default=5)
    round_duration = db.Column(db.Integer, default=60)
    max_players = db.Column(db.Integer, default=8)
    status = db.Column(db.String(20), default="WAITING") # WAITING, PLAYING, FINISHED
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    scores = db.relationship("GameScore", backref="room", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "room_code": self.room_code,
            "host_name": self.host_name,
            "category": self.category,
            "rounds": self.rounds,
            "round_duration": self.round_duration,
            "max_players": self.max_players,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class GameScore(db.Model):
    __tablename__ = "game_scores"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    player_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, default=0)
    correct_guesses = db.Column(db.Integer, default=0)
    rounds_drawn = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "player_name": self.player_name,
            "score": self.score,
            "correct_guesses": self.correct_guesses,
            "rounds_drawn": self.rounds_drawn,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
