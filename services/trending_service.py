import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TrendingService:
    """
    Service to provide trending English songs.
    Designed with an adapter architecture:
    - Default/Fallback: Curated seeded songs in database
    - Dynamic Chart Source: Extensible hook for external API (e.g., Billboard, Last.fm, Spotify)
    """
    _cached_trending: List[Dict[str, Any]] = []
    _last_fetched: datetime = None
    _cache_duration = timedelta(hours=6)

    @classmethod
    def get_trending_songs(cls, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Retrieve current trending English songs."""
        now = datetime.utcnow()
        if (
            not force_refresh 
            and cls._cached_trending 
            and cls._last_fetched 
            and (now - cls._last_fetched) < cls._cache_duration
        ):
            return cls._cached_trending

        # Attempt to fetch from external chart provider if configured
        external_songs = cls._fetch_external_chart_data()
        if external_songs:
            cls._cached_trending = external_songs
            cls._last_fetched = now
            return cls._cached_trending

        # Fallback to database seeded trending songs
        from models import Song
        try:
            db_songs = Song.query.filter_by(category="Trending", active=True).all()
            if db_songs:
                cls._cached_trending = [s.to_dict(include_secret=True) for s in db_songs]
                cls._last_fetched = now
                return cls._cached_trending
        except Exception as e:
            logger.warning(f"Could not load trending songs from DB: {e}")

        # Static fallback list if DB not ready
        return [
            {"title": "Espresso", "artist": "Sabrina Carpenter", "category": "Trending", "difficulty": "EASY", "year": 2024},
            {"title": "Flowers", "artist": "Miley Cyrus", "category": "Trending", "difficulty": "EASY", "year": 2023},
            {"title": "Cruel Summer", "artist": "Taylor Swift", "category": "Trending", "difficulty": "MEDIUM", "year": 2023},
            {"title": "Birds of a Feather", "artist": "Billie Eilish", "category": "Trending", "difficulty": "MEDIUM", "year": 2024},
            {"title": "Greedy", "artist": "Tate McRae", "category": "Trending", "difficulty": "MEDIUM", "year": 2023},
            {"title": "Vampire", "artist": "Olivia Rodrigo", "category": "Trending", "difficulty": "EASY", "year": 2023}
        ]

    @classmethod
    def _fetch_external_chart_data(cls) -> List[Dict[str, Any]]:
        """
        Hook for future legitimate chart API integration.
        Returns empty list when external credentials are not configured.
        """
        # Designed so developers can plug in a licensed chart API key in .env
        return []
