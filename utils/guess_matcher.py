import re
import unicodedata
from difflib import SequenceMatcher

def normalize_text(text: str) -> str:
    """
    Normalize text for comparison:
    - lowercase
    - strip diacritics / accents
    - remove punctuation and special characters
    - collapse whitespace
    """
    if not text:
        return ""
        
    # Decompose unicode characters (e.g., é -> e)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    
    # Remove apostrophes without space so "can't" matches "cant"
    text = re.sub(r"['’`]", "", text)

    # Replace other punctuation with space
    text = re.sub(r"[^\w\s]", " ", text)
    
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
        
    if len(s2) == 0:
        return len(s1)
        
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def check_guess(guess: str, title: str, artist: str = None, movie: str = None) -> dict:
    """
    Authoritatively check player's guess against secret song metadata.
    Returns:
        {
            "is_correct": bool,
            "is_close": bool,
            "is_artist": bool,
            "is_movie": bool,
            "feedback": str
        }
    """
    norm_guess = normalize_text(guess)
    norm_title = normalize_text(title)
    
    if not norm_guess:
        return {
            "is_correct": False,
            "is_close": False,
            "is_artist": False,
            "is_movie": False,
            "feedback": ""
        }
        
    # 1. Exact or normalized match
    if norm_guess == norm_title:
        return {
            "is_correct": True,
            "is_close": False,
            "is_artist": False,
            "is_movie": False,
            "feedback": "Correct!"
        }
        
    # Also handle without leading 'the ' or 'a ' if title begins with it
    strip_articles = lambda s: re.sub(r"^(the|a|an)\s+", "", s)
    if strip_articles(norm_guess) == strip_articles(norm_title) and len(strip_articles(norm_guess)) > 2:
        return {
            "is_correct": True,
            "is_close": False,
            "is_artist": False,
            "is_movie": False,
            "feedback": "Correct!"
        }
        
    # 2. Check if player guessed the artist
    if artist:
        norm_artist = normalize_text(artist)
        if norm_guess == norm_artist or (len(norm_guess) >= 4 and norm_guess in norm_artist):
            return {
                "is_correct": False,
                "is_close": False,
                "is_artist": True,
                "is_movie": False,
                "feedback": f"'{guess}' is the artist! Now guess the song title!"
            }
            
    # 3. Check if player guessed the movie (for Hollywood songs)
    if movie:
        norm_movie = normalize_text(movie)
        if norm_guess == norm_movie:
            return {
                "is_correct": False,
                "is_close": False,
                "is_artist": False,
                "is_movie": True,
                "feedback": f"'{guess}' is the movie soundtrack! What's the song title?"
            }
            
    # 4. Check if close to title (Levenshtein distance <= 2 or similarity ratio >= 0.84)
    dist = levenshtein_distance(norm_guess, norm_title)
    ratio = SequenceMatcher(None, norm_guess, norm_title).ratio()
    
    is_close = False
    if len(norm_title) > 3:
        if dist <= 2 or ratio >= 0.84:
            is_close = True
            
    return {
        "is_correct": False,
        "is_close": is_close,
        "is_artist": False,
        "is_movie": False,
        "feedback": "You are very close!" if is_close else ""
    }
