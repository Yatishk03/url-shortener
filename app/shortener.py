# Base62 encoding — the core algorithm
# Converts a numeric ID to a short string like "aB3xZ"
# Amazon interviewers WILL ask you to explain this

ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
BASE = len(ALPHABET)  # 62


def encode(num: int) -> str:
    """Convert integer ID → Base62 short code."""
    if num == 0:
        return ALPHABET[0]
    
    result = []
    while num:
        result.append(ALPHABET[num % BASE])
        num //= BASE
    
    return "".join(reversed(result))


def decode(short_code: str) -> int:
    """Convert Base62 short code → integer ID."""
    num = 0
    for char in short_code:
        num = num * BASE + ALPHABET.index(char)
    return num