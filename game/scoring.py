import math

class ScoringEngine:
    """
    Authoritative server-side scoring calculations.
    """
    BASE_SCORE = 1000
    MIN_GUESS_SCORE = 150
    DRAWER_BONUS_PER_GUESS = 250
    FIRST_GUESS_BONUS = 150

    DIFFICULTY_MULTIPLIERS = {
        "EASY": 1.0,
        "MEDIUM": 1.15,
        "HARD": 1.3
    }

    @classmethod
    def calculate_guess_score(
        cls, 
        time_remaining: float, 
        total_time: float, 
        difficulty: str = "MEDIUM",
        guess_rank: int = 1
    ) -> int:
        """
        Calculate points awarded to a player for guessing correctly.
        - Higher points for faster response (ratio of time_remaining / total_time).
        - Multiplier for difficulty.
        - Bonus for first guesser.
        """
        if total_time <= 0:
            return cls.MIN_GUESS_SCORE

        # Time decay ratio between 0.0 and 1.0
        ratio = max(0.0, min(1.0, time_remaining / total_time))
        
        # Non-linear curve (square root gives gentle drop-off so good guesses still score well)
        decay_factor = math.sqrt(ratio)
        
        raw_score = cls.BASE_SCORE * decay_factor
        diff_multiplier = cls.DIFFICULTY_MULTIPLIERS.get(difficulty.upper(), 1.0)
        final_score = raw_score * diff_multiplier

        # Rank bonus (1st player to guess gets an extra bonus)
        if guess_rank == 1:
            final_score += cls.FIRST_GUESS_BONUS
        elif guess_rank == 2:
            final_score += int(cls.FIRST_GUESS_BONUS * 0.5)

        return max(cls.MIN_GUESS_SCORE, int(final_score))

    @classmethod
    def calculate_drawer_score(
        cls, 
        correct_guess_count: int, 
        total_guessers: int
    ) -> int:
        """
        Calculate points awarded to the drawer at round end based on
        how many players were able to guess their drawing.
        """
        if total_guessers <= 0 or correct_guess_count <= 0:
            return 0
            
        success_ratio = correct_guess_count / total_guessers
        base_bonus = correct_guess_count * cls.DRAWER_BONUS_PER_GUESS
        
        # Perfect round bonus if all active guessers guessed
        if success_ratio >= 1.0:
            base_bonus += 200

        return int(base_bonus)
