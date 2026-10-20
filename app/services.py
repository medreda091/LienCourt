"""Business logic: base62 encoding and short-code generation."""

import secrets
import string

from sqlalchemy.orm import Session

from app.models import Link

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
DEFAULT_CODE_LENGTH = 6
_MAX_ATTEMPTS = 10


def encode_base62(num: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if num < 0:
        raise ValueError("num must be non-negative")
    if num == 0:
        return BASE62_ALPHABET[0]
    digits: list[str] = []
    base = len(BASE62_ALPHABET)
    while num:
        num, rem = divmod(num, base)
        digits.append(BASE62_ALPHABET[rem])
    return "".join(reversed(digits))


def decode_base62(code: str) -> int:
    """Decode a base62 string back to an integer."""
    base = len(BASE62_ALPHABET)
    value = 0
    for char in code:
        value = value * base + BASE62_ALPHABET.index(char)
    return value


def generate_random_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """Return a cryptographically random base62 code."""
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


def generate_unique_code(db: Session, length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generate a code that does not already exist in the database."""
    for _ in range(_MAX_ATTEMPTS):
        code = generate_random_code(length)
        if db.query(Link).filter(Link.code == code).first() is None:
            return code
    # Extremely unlikely: grow the code by one character and retry.
    return generate_unique_code(db, length + 1)


def get_link_by_code(db: Session, code: str) -> Link | None:
    return db.query(Link).filter(Link.code == code).first()
