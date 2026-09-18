import unittest
from flask import Flask
from config import TestingConfig
from models import db, Song

class TestSongModel(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.from_object(TestingConfig)
        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()
            # Add sample test songs
            s1 = Song(title="Bohemian Rhapsody", artist="Queen", category="English", difficulty="MEDIUM", year=1975)
            s2 = Song(title="My Heart Will Go On", artist="Celine Dion", category="Hollywood", movie="Titanic", difficulty="EASY", year=1997)
            s3 = Song(title="Espresso", artist="Sabrina Carpenter", category="Trending", difficulty="EASY", year=2024)
            db.session.add_all([s1, s2, s3])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_category_filtering(self):
        with self.app.app_context():
            hollywood = Song.query.filter_by(category="Hollywood").all()
            self.assertEqual(len(hollywood), 1)
            self.assertEqual(hollywood[0].movie, "Titanic")

            english = Song.query.filter_by(category="English").all()
            self.assertEqual(len(english), 1)
            self.assertEqual(english[0].artist, "Queen")

    def test_masked_title(self):
        with self.app.app_context():
            song = Song.query.filter_by(title="Bohemian Rhapsody").first()
            masked = song.masked_title()
            self.assertNotIn("Bohemian", masked)
            self.assertNotIn("Rhapsody", masked)
            self.assertIn("_", masked)

    def test_to_dict_secret_isolation(self):
        with self.app.app_context():
            song = Song.query.first()
            public_dict = song.to_dict(include_secret=False)
            self.assertNotIn("title", public_dict)
            self.assertIn("artist", public_dict)

            secret_dict = song.to_dict(include_secret=True)
            self.assertIn("title", secret_dict)

if __name__ == "__main__":
    unittest.main()
