import random
import string
import re

# Readable character set excluding confusing characters (0/O, 1/I)
ROOM_CODE_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def generate_room_code(length: int = 5, existing_codes: set = None) -> str:
    """Generate a random collision-resistant room code (e.g. X7K92)."""
    if existing_codes is None:
        existing_codes = set()
    
    max_attempts = 100
    for _ in range(max_attempts):
        code = "".join(random.choices(ROOM_CODE_CHARS, k=length))
        if code not in existing_codes:
            return code
            
    # Fallback to longer code if space is dense
    return "".join(random.choices(ROOM_CODE_CHARS, k=length + 1))

def sanitize_string(text: str, max_length: int = 100) -> str:
    """Sanitize string input, trimming whitespace and limiting length."""
    if not text:
        return ""
    # Strip HTML tags and control chars
    clean = re.sub(r"<[^>]*>", "", text)
    clean = clean.strip()
    return clean[:max_length]
