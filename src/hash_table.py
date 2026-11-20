"""A string-keyed hash table using separate chaining and Horner hashing."""

import math


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key: str, value: str, next_node: "_Node | None" = None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """Store string keys and values in buckets with linked-list collision chains."""

    HORNER_MULTIPLIER = 257

    def __init__(self, capacity: int = 11, max_load: float | None = 0.75):
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if max_load is not None:
            if (
                isinstance(max_load, bool)
                or not isinstance(max_load, (int, float))
            ):
                raise TypeError("max_load must be a positive number or None")
            if not math.isfinite(max_load) or max_load <= 0:
                raise ValueError("max_load must be a positive finite number")

        self.capacity = capacity
        self.max_load = max_load
        self._buckets: list[_Node | None] = [None] * capacity
        self._size = 0
        self.last_probes = 0

    @property
    def load_factor(self) -> float:
        return self._size / self.capacity

    def hash_steps(self, key: str) -> tuple[tuple[str, int], ...]:
        """Return each character and its intermediate Horner hash value."""
        self._validate_key(key)
        value = 0
        steps = []
        for character in key:
            value = (value * self.HORNER_MULTIPLIER + ord(character)) % self.capacity
            steps.append((character, value))
        return tuple(steps)

    def _index(self, key: str) -> int:
        self._validate_key(key)
        value = 0
        for character in key:
            value = (value * self.HORNER_MULTIPLIER + ord(character)) % self.capacity
        return value

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    @staticmethod
    def _validate_pair(key: str, value: str) -> None:
        HashTable._validate_key(key)
        if not isinstance(value, str):
            raise TypeError("value must be a string")

    def put(self, key: str, value: str) -> None:
        """Insert or replace a key-value pair."""
        self._validate_pair(key, value)
        index = self._index(key)
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next

        self._buckets[index] = _Node(key, value, self._buckets[index])
        self._size += 1
        if self.max_load is not None and self.load_factor > self.max_load:
            self._resize(self.capacity * 2 + 1)

    def get(self, key: str) -> str | None:
        """Return the value for key, or None when key is absent."""
        self.last_probes = 0
        index = self._index(key)
        node = self._buckets[index]
        while node is not None:
            self.last_probes += 1
            if node.key == key:
                return node.value
            node = node.next
        return None

    def remove(self, key: str) -> bool:
        """Remove key and report whether it was present."""
        index = self._index(key)
        previous = None
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                if previous is None:
                    self._buckets[index] = node.next
                else:
                    previous.next = node.next
                self._size -= 1
                return True
            previous = node
            node = node.next
        return False

    def items(self):
        """Iterate over stored key-value pairs."""
        for bucket in self._buckets:
            node = bucket
            while node is not None:
                yield node.key, node.value
                node = node.next

    def slots(self) -> tuple[tuple[tuple[str, str], ...], ...]:
        """Return the bucket contents as immutable key-value sequences."""
        buckets = []
        for bucket in self._buckets:
            entries = []
            node = bucket
            while node is not None:
                entries.append((node.key, node.value))
                node = node.next
            buckets.append(tuple(entries))
        return tuple(buckets)

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self.capacity = new_capacity
        self._buckets = [None] * new_capacity
        for bucket in old_buckets:
            node = bucket
            while node is not None:
                index = self._index(node.key)
                self._buckets[index] = _Node(
                    node.key, node.value, self._buckets[index]
                )
                node = node.next
