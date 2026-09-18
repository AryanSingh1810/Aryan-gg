import re
from typing import Tuple, Optional
from config import Config

def validate_player_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate player display name."""
    if not name or not isinstance(name, str):
        return False, "Player name cannot be empty."
    
    clean_name = name.strip()
    if len(clean_name) < 2:
        return False, "Player name must be at least 2 characters."
    if len(clean_name) > 20:
        return False, "Player name cannot exceed 20 characters."
    
    # Allow alphanumeric, spaces, and basic underscores/hyphens
    if not re.match(r"^[a-zA-Z0-9 _-]+$", clean_name):
        return False, "Player name can only contain letters, numbers, spaces, and hyphens."
        
    return True, None

def validate_room_settings(
    category: str, 
    rounds: int, 
    round_duration: int, 
    max_players: int,
    mode: str = "song"
) -> Tuple[bool, Optional[str]]:
    """Validate room creation settings."""
    valid_categories = Config.GAME_MODES.get(mode, {}).get("categories") if hasattr(Config, "GAME_MODES") else Config.CATEGORIES
    if not valid_categories:
        valid_categories = ["English", "Hollywood", "Trending", "Popular", "Classic"]
    if category not in valid_categories:
        return False, f"Invalid category for {mode} mode. Must be one of: {', '.join(valid_categories)}."
    
    try:
        rounds = int(rounds)
        round_duration = int(round_duration)
        max_players = int(max_players)
    except (ValueError, TypeError):
        return False, "Room parameters must be numeric integers."
        
    if not (Config.MIN_ROUNDS <= rounds <= Config.MAX_ROUNDS):
        return False, f"Rounds must be between {Config.MIN_ROUNDS} and {Config.MAX_ROUNDS}."
        
    if not (Config.MIN_ROUND_DURATION <= round_duration <= Config.MAX_ROUND_DURATION):
        return False, f"Round duration must be between {Config.MIN_ROUND_DURATION} and {Config.MAX_ROUND_DURATION} seconds."
        
    if not (Config.MIN_PLAYERS <= max_players <= Config.MAX_PLAYERS):
        return False, f"Max players must be between {Config.MIN_PLAYERS} and {Config.MAX_PLAYERS}."
        
    return True, None
