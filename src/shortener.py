"""URL shortening backed by the project's custom hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable
from src.linear_probing_hash_table import LinearProbingHashTable


class URLShortener:
    """Create stable base62 codes for valid HTTP(S) URLs."""

    def __init__(self, strategy: str = "chaining"):
        if strategy == "chaining":
            table_type = HashTable
        elif strategy == "linear":
            table_type = LinearProbingHashTable
        else:
            raise ValueError("strategy must be 'chaining' or 'linear'")

        self.strategy = strategy
        self._url_to_code = table_type()
        self._code_to_url = table_type()
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

    def table_snapshot(
        self,
        strategy: str | None = None,
    ) -> tuple[int, float, tuple[tuple[tuple[str, str], ...], ...]]:
        """Return a table snapshot using the requested collision strategy."""
        requested_strategy = self.strategy if strategy is None else strategy
        if requested_strategy == self.strategy:
            table = self._url_to_code
        elif requested_strategy == "chaining":
            table = HashTable(
                capacity=self._url_to_code.capacity,
                max_load=self._url_to_code.max_load,
            )
        elif requested_strategy == "linear":
            table = LinearProbingHashTable(
                capacity=self._url_to_code.capacity,
                max_load=self._url_to_code.max_load,
            )
        else:
            raise ValueError("strategy must be 'chaining' or 'linear'")

        if requested_strategy != self.strategy:
            for url, code in self._url_to_code.items():
                table.put(url, code)

        return (
            table.capacity,
            table.load_factor,
            table.slots(),
        )

    def hash_steps(self, url: str) -> tuple[tuple[str, int], ...]:
        """Return the table's Horner hash steps for a URL key."""
        return self._url_to_code.hash_steps(url)
