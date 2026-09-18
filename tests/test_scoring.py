import unittest
from game.scoring import ScoringEngine

class TestScoringEngine(unittest.TestCase):
    def test_fast_guess_higher_score(self):
        fast_score = ScoringEngine.calculate_guess_score(
            time_remaining=55,
            total_time=60,
            difficulty="MEDIUM",
            guess_rank=1
        )
        slow_score = ScoringEngine.calculate_guess_score(
            time_remaining=10,
            total_time=60,
            difficulty="MEDIUM",
            guess_rank=3
        )
        self.assertGreater(fast_score, slow_score)

    def test_difficulty_multipliers(self):
        easy_score = ScoringEngine.calculate_guess_score(30, 60, "EASY", 1)
        hard_score = ScoringEngine.calculate_guess_score(30, 60, "HARD", 1)
        self.assertGreater(hard_score, easy_score)

    def test_minimum_score_guaranteed(self):
        min_score = ScoringEngine.calculate_guess_score(0, 60, "EASY", 5)
        self.assertEqual(min_score, ScoringEngine.MIN_GUESS_SCORE)

    def test_drawer_score(self):
        # 3 out of 3 guessers guessed correctly
        drawer_perfect = ScoringEngine.calculate_drawer_score(3, 3)
        # 1 out of 3 guessers
        drawer_partial = ScoringEngine.calculate_drawer_score(1, 3)
        self.assertGreater(drawer_perfect, drawer_partial)

        # 0 guessers
        drawer_zero = ScoringEngine.calculate_drawer_score(0, 3)
        self.assertEqual(drawer_zero, 0)

if __name__ == "__main__":
    unittest.main()
