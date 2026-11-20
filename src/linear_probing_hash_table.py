"""A linear-probing hash table that reuses HashTable's Horner hash."""

from collections.abc import Iterator

from src.hash_table import HashTable, _Node


class _Tombstone(_Node):
    __slots__ = ()


_TOMBSTONE = _Tombstone("", "")


class LinearProbingHashTable(HashTable):
    """Store string key-value pairs with cyclic linear probing."""

    def put(self, key: str, value: str) -> None:
        """Insert or replace a pair, reusing deleted slots when possible."""
        self._validate_pair(key, value)
        first_tombstone = None
        start = self._index(key)

        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            node = self._buckets[index]
            if node is _TOMBSTONE:
                if first_tombstone is None:
                    first_tombstone = index
                continue
            if node is None:
                target = first_tombstone if first_tombstone is not None else index
                self._buckets[target] = _Node(key, value)
                self._size += 1
                self._resize_if_needed()
                return
            if node.key == key:
                node.value = value
                return

        if first_tombstone is not None:
            self._buckets[first_tombstone] = _Node(key, value)
            self._size += 1
            self._resize_if_needed()
            return
        raise OverflowError("hash table is full")

    def get(self, key: str) -> str | None:
        """Return the value for key, or None when key is absent."""
        self.last_probes = 0
        start = self._index(key)
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            node = self._buckets[index]
            if node is None:
                return None
            self.last_probes += 1
            if node is not _TOMBSTONE and node.key == key:
                return node.value
        return None

    def remove(self, key: str) -> bool:
        """Mark a matching slot as deleted without breaking its probe chain."""
        start = self._index(key)
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            node = self._buckets[index]
            if node is None:
                return False
            if node is not _TOMBSTONE and node.key == key:
                self._buckets[index] = _TOMBSTONE
                self._size -= 1
                return True
        return False

    def items(self) -> Iterator[tuple[str, str]]:
        """Iterate over live key-value pairs."""
        for node in self._buckets:
            if node is not None and node is not _TOMBSTONE:
                yield node.key, node.value

    def slots(self) -> tuple[tuple[tuple[str, str], ...], ...]:
        """Return a bucket-compatible snapshot of the occupied slots."""
        return tuple(
            ((node.key, node.value),)
            if node is not None and node is not _TOMBSTONE
            else ()
            for node in self._buckets
        )

    def _resize_if_needed(self) -> None:
        if self.max_load is not None and self.load_factor > self.max_load:
            self._resize(self.capacity * 2 + 1)

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self.capacity = new_capacity
        self._buckets = [None] * new_capacity
        self._size = 0
        for node in old_buckets:
            if node is not None and node is not _TOMBSTONE:
                self._insert_without_resize(node.key, node.value)

    def _insert_without_resize(self, key: str, value: str) -> None:
        start = self._index(key)
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            if self._buckets[index] is None:
                self._buckets[index] = _Node(key, value)
                self._size += 1
                return
        raise RuntimeError("resized table has no free slot")
