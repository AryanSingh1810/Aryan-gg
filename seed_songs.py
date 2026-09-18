import os
import json
from pathlib import Path
from flask import Flask
from config import config_by_name
from models import db, Song, User

def seed_database(env: str = "default"):
    """Populate database tables and seed initial songs."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[env])
    db.init_app(app)

    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        # Seed songs from data/songs.json
        data_path = Path(__file__).resolve().parent / "data" / "songs.json"
        if not data_path.exists():
            print(f"Error: {data_path} not found.")
            return

        with open(data_path, "r", encoding="utf-8") as f:
            songs_data = json.load(f)

        count_added = 0
        count_updated = 0
        for item in songs_data:
            existing = Song.query.filter_by(title=item["title"], artist=item["artist"]).first()
            if existing:
                existing.category = item.get("category", "English")
                existing.difficulty = item.get("difficulty", "MEDIUM")
                existing.year = item.get("year")
                existing.movie = item.get("movie")
                existing.keywords = item.get("keywords")
                existing.active = True
                count_updated += 1
            else:
                song = Song(
                    title=item["title"],
                    artist=item["artist"],
                    category=item.get("category", "English"),
                    difficulty=item.get("difficulty", "MEDIUM"),
                    year=item.get("year"),
                    movie=item.get("movie"),
                    keywords=item.get("keywords"),
                    active=True
                )
                db.session.add(song)
                count_added += 1

        db.session.commit()
        total = Song.query.count()
        print(f"Database seeded successfully! Added: {count_added}, Updated: {count_updated}, Total songs: {total}")

if __name__ == "__main__":
    seed_database()
