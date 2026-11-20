"""URL shortening backed by the project's custom hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable


class URLShortener:
    """Create stable base62 codes for valid HTTP(S) URLs."""

    def __init__(self):
        self._url_to_code = HashTable()
        self._code_to_url = HashTable()
        self._next_id = 0

    @staticmethod
    def _validate_url(url: str) -> None:
        if not isinstance(url, str):
            raise ValueError("URL must be a string")
        if not url or url != url.strip():
            raise ValueError("URL must not be empty or have surrounding whitespace")

        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("URL is malformed") from error

        if parsed.scheme.lower() not in ("http", "https") or not hostname:
            raise ValueError("URL must have an HTTP(S) scheme and host")

    def shorten(self, url: str) -> str:
        """Return the existing or newly assigned code for a valid URL."""
        self._validate_url(url)
        existing_code = self._url_to_code.get(url)
        if existing_code is not None:
            return existing_code

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.put(url, code)
        self._code_to_url.put(code, url)
        return code

    def expand(self, code: str) -> str:
        """Return the original URL for code, raising KeyError if unknown."""
        url = self._code_to_url.get(code)
        if url is None:
            raise KeyError(code)
        return url
