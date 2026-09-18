from flask import Blueprint, jsonify, request
from models import Song
from services.trending_service import TrendingService

song_bp = Blueprint("songs", __name__, url_prefix="/api")

@song_bp.route("/songs")
def list_songs():
    """List active songs with category and difficulty filters (excluding secret answers in public API)."""
    category = request.args.get("category")
    difficulty = request.args.get("difficulty")

    query = Song.query.filter_by(active=True)
    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    songs = query.all()
    # Mask secrets for public read API
    data = [{
        "id": s.id,
        "artist": s.artist,
        "category": s.category,
        "difficulty": s.difficulty,
        "movie": s.movie,
        "year": s.year
    } for s in songs]

    return jsonify({"count": len(data), "songs": data})

@song_bp.route("/trending")
def trending_songs():
    """Get dynamic list of trending songs."""
    trending = TrendingService.get_trending_songs()
    # Mask title in public API
    safe_data = [{
        "artist": s.get("artist"),
        "category": s.get("category"),
        "difficulty": s.get("difficulty"),
        "year": s.get("year")
    } for s in trending]
    return jsonify({"count": len(safe_data), "songs": safe_data})
