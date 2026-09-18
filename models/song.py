from datetime import datetime, timezone
from models import db

def utc_now():
    return datetime.now(timezone.utc)

class Song(db.Model):
    __tablename__ = "songs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    artist = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True) # English, Hollywood, Trending
    difficulty = db.Column(db.String(20), default="MEDIUM")          # EASY, MEDIUM, HARD
    year = db.Column(db.Integer, nullable=True)
    movie = db.Column(db.String(150), nullable=True)                 # For Hollywood category
    keywords = db.Column(db.String(255), nullable=True)              # Visual hints / theme tags
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def to_dict(self, include_secret: bool = True):
        """Serialize song. If include_secret is False, title and keywords are omitted or masked."""
        data = {
            "id": self.id,
            "artist": self.artist,
            "category": self.category,
            "difficulty": self.difficulty,
            "year": self.year,
            "movie": self.movie,
        }
        if include_secret:
            data["title"] = self.title
            data["keywords"] = self.keywords
        return data

    def masked_title(self) -> str:
        """Returns masked display of song title, e.g. 'B _ _ _ _ _ _   L _ _ _ _ _' or word structure."""
        masked_words = []
        for word in self.title.split():
            chars = []
            for i, c in enumerate(word):
                if c.isalnum():
                    chars.append("_")
                else:
                    chars.append(c)
            masked_words.append(" ".join(chars))
        return "   ".join(masked_words)
