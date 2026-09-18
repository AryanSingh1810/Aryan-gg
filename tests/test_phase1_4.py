import unittest
import json
from pathlib import Path
from app import create_app
from config import Config
from utils.validators import validate_room_settings, validate_player_name

class TestPhase1To4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app("testing")
        cls.client = cls.app.test_client()

    def test_app_branding_and_config(self):
        """Phase 1: Verify branding constants and GAME_MODES config."""
        self.assertEqual(Config.APP_NAME, "DRAW & GUESS")
        self.assertEqual(Config.APP_TAGLINE, "Draw it. Guess it. Win it.")
        self.assertIn("song", Config.GAME_MODES)
        self.assertIn("movie", Config.GAME_MODES)
        self.assertIn("English", Config.GAME_MODES["song"]["categories"])
        self.assertIn("Hollywood", Config.GAME_MODES["movie"]["categories"])
        self.assertIn("Classic", Config.GAME_MODES["movie"]["categories"])

    def test_movies_dataset_exists_and_valid(self):
        """Phase 1: Verify data/movies.json format and categories."""
        movies_path = Path(__file__).resolve().parent.parent / "data" / "movies.json"
        self.assertTrue(movies_path.exists())
        with open(movies_path, "r", encoding="utf-8") as f:
            movies = json.load(f)
        self.assertGreater(len(movies), 10)
        categories = {m["category"] for m in movies}
        self.assertTrue({"Hollywood", "Trending", "Popular", "Classic"}.issubset(categories))
        for m in movies:
            self.assertIn("title", m)
            self.assertIn("year", m)
            self.assertIn("genre", m)
            self.assertIn("keywords", m)
            self.assertTrue(m["active"])

    def test_homepage_render(self):
        """Phase 3: Verify professional homepage content and structure."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("DRAW", html)
        self.assertIn("&amp; GUESS", html)
        self.assertIn("Draw it. <span>Guess it.</span> Win it.", html)
        self.assertIn("GUESS THE SONG", html)
        self.assertIn("GUESS THE MOVIE", html)
        self.assertIn("How It Works", html)
        self.assertIn("Choose a Mode", html)
        self.assertIn("Create or Join", html)
        self.assertIn("One Player Draws", html)
        self.assertIn("Everyone Guesses", html)
        self.assertIn("Fastest Score More", html)
        self.assertIn("Highest Score Wins", html)
        self.assertIn("Two Immersive Entertainment Arenas", html)
        self.assertIn("Real-Time Multiplayer", html)
        self.assertIn("Drawing Canvas", html)
        self.assertIn("Live Guessing", html)
        self.assertIn("Competitive Scoring", html)
        self.assertIn("Private Rooms", html)
        self.assertIn("Leaderboards", html)
        self.assertIn("Trending Content", html)

    def test_mode_selection_page(self):
        """Phase 4: Verify mode selection page displays both Song and Movie cards."""
        res = self.client.get("/modes")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Select Your Game Mode", html)
        self.assertIn("GUESS THE SONG", html)
        self.assertIn("GUESS THE MOVIE", html)
        self.assertIn("English Pop &amp; Rock", html)
        self.assertIn("Hollywood Soundtracks", html)
        self.assertIn("Hollywood Blockbusters", html)
        self.assertIn("Timeless Classics", html)
        self.assertIn("Upcoming Future Arenas", html)

    def test_create_room_song_and_movie_modes(self):
        """Verify create room renders correctly for both modes."""
        res_song = self.client.get("/create-room?mode=song")
        self.assertEqual(res_song.status_code, 200)
        self.assertIn("Song Category", res_song.data.decode("utf-8"))

        res_movie = self.client.get("/create-room?mode=movie")
        self.assertEqual(res_movie.status_code, 200)
        self.assertIn("Movie Category", res_movie.data.decode("utf-8"))
        self.assertIn("Blockbusters & Sci-Fi", res_movie.data.decode("utf-8"))

    def test_settings_validators_for_modes(self):
        """Verify room validator validates categories for both modes."""
        ok_song, err_song = validate_room_settings("English", 5, 60, 8, mode="song")
        self.assertTrue(ok_song)
        self.assertIsNone(err_song)

        ok_movie, err_movie = validate_room_settings("Classic", 5, 60, 8, mode="movie")
        self.assertTrue(ok_movie)
        self.assertIsNone(err_movie)

        invalid_movie, err_inv = validate_room_settings("NotARealCategory", 5, 60, 8, mode="movie")
        self.assertFalse(invalid_movie)
        self.assertIsNotNone(err_inv)

if __name__ == "__main__":
    unittest.main()
