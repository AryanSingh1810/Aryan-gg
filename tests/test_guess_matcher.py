import unittest
from utils.guess_matcher import check_guess, normalize_text

class TestGuessMatcher(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize_text("  Blinding   Lights!  "), "blinding lights")
        self.assertEqual(normalize_text("Sweet Child O' Mine"), "sweet child o mine")

    def test_exact_match(self):
        res = check_guess("blinding lights", "Blinding Lights")
        self.assertTrue(res["is_correct"])

        res2 = check_guess("BLINDING LIGHTS", "Blinding Lights")
        self.assertTrue(res2["is_correct"])

    def test_punctuation_insensitivity(self):
        res = check_guess("cant stop the feeling", "Can't Stop the Feeling!")
        self.assertTrue(res["is_correct"])

    def test_close_guess_feedback(self):
        # Typo: "blinding light" vs "blinding lights" (missing 's')
        res = check_guess("blinding light", "Blinding Lights")
        self.assertFalse(res["is_correct"])
        self.assertTrue(res["is_close"])

    def test_artist_hint(self):
        res = check_guess("the weeknd", "Blinding Lights", artist="The Weeknd")
        self.assertFalse(res["is_correct"])
        self.assertTrue(res["is_artist"])
        self.assertIn("artist", res["feedback"])

    def test_movie_soundtrack_hint(self):
        res = check_guess("titanic", "My Heart Will Go On", artist="Celine Dion", movie="Titanic")
        self.assertFalse(res["is_correct"])
        self.assertTrue(res["is_movie"])
        self.assertIn("soundtrack", res["feedback"])

if __name__ == "__main__":
    unittest.main()
