"""Base62 encoding using the digits 0-9, lowercase a-z, and uppercase A-Z."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(number: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if not isinstance(number, int) or isinstance(number, bool):
        raise TypeError("number must be an integer")
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return ALPHABET[0]

    encoded = []
    while number:
        number, remainder = divmod(number, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(code: str) -> int:
    """Decode a non-empty base62 string to a non-negative integer."""
    if not isinstance(code, str):
        raise TypeError("code must be a string")
    if not code:
        raise ValueError("code must not be empty")

    value = 0
    for character in code:
        digit = ALPHABET.find(character)
        if digit < 0:
            raise ValueError(f"invalid base62 character: {character!r}")
        value = value * BASE + digit
    return value
