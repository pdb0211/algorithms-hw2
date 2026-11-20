import unittest

from src.hash_table import HashTable, LinearProbingHashTable


def _keys_for_bucket(table, bucket_index, count):
    keys = []
    for codepoint in range(32, 127):
        key = chr(codepoint)
        steps = table.hash_steps(key)
        if steps and steps[-1][1] == bucket_index:
            keys.append(key)
            if len(keys) == count:
                return keys
    raise AssertionError(f"could not find {count} keys for bucket {bucket_index}")


class HashTableTests(unittest.TestCase):
    def test_empty_table_lookup_and_remove(self):
        table = HashTable()

        self.assertIsNone(table.get("missing"))
        self.assertFalse(table.remove("missing"))

    def test_colliding_keys_can_be_updated_and_removed_independently(self):
        table = HashTable()
        table.put("a", "first")
        table.put("l", "second")

        self.assertEqual(table.get("a"), "first")
        self.assertEqual(table.get("l"), "second")

        table.put("a", "updated")
        self.assertEqual(table.get("a"), "updated")
        self.assertTrue(table.remove("a"))
        self.assertIsNone(table.get("a"))
        self.assertEqual(table.get("l"), "second")

    def test_resize_preserves_all_entries(self):
        table = HashTable()
        initial_capacity = table.capacity

        for index in range(9):
            table.put(f"url-{index}", f"code-{index}")

        self.assertGreater(table.capacity, initial_capacity)
        for index in range(9):
            with self.subTest(index=index):
                self.assertEqual(table.get(f"url-{index}"), f"code-{index}")

    def test_items_contains_all_stored_pairs(self):
        table = HashTable()
        expected = [(f"key-{index}", f"value-{index}") for index in range(5)]
        for key, value in expected:
            table.put(key, value)

        self.assertCountEqual(table.items(), expected)

    def test_none_max_load_disables_resize(self):
        table = HashTable(capacity=3, max_load=None)

        for index in range(10):
            table.put(f"key-{index}", f"value-{index}")

        self.assertEqual(table.capacity, 3)
        self.assertEqual(table.load_factor, 10 / 3)

    def test_get_records_nodes_compared(self):
        table = HashTable()
        table.put("a", "first")
        table.put("l", "second")

        self.assertEqual(table.get("l"), "second")
        self.assertEqual(table.last_probes, 1)
        self.assertEqual(table.get("a"), "first")
        self.assertEqual(table.last_probes, 2)
        self.assertIsNone(table.get("w"))
        self.assertEqual(table.last_probes, 2)


class LinearProbingHashTableTests(unittest.TestCase):
    def test_collisions_wrap_from_last_slot_to_zero(self):
        table = LinearProbingHashTable(capacity=5, max_load=None)
        keys = _keys_for_bucket(table, 4, 3)

        for index, key in enumerate(keys):
            table.put(key, f"value-{index}")

        slots = table.slots()
        self.assertEqual(slots[4], ((keys[0], "value-0"),))
        self.assertEqual(slots[0], ((keys[1], "value-1"),))
        self.assertEqual(slots[1], ((keys[2], "value-2"),))
        for index, key in enumerate(keys):
            with self.subTest(key=key):
                self.assertEqual(table.get(key), f"value-{index}")

    def test_lookup_continues_past_tombstone_and_updates_later_key(self):
        table = LinearProbingHashTable(capacity=5, max_load=None)
        keys = _keys_for_bucket(table, 4, 3)
        for index, key in enumerate(keys):
            table.put(key, f"value-{index}")

        self.assertTrue(table.remove(keys[1]))
        self.assertEqual(table.get(keys[2]), "value-2")

        table.put(keys[2], "updated")
        self.assertEqual(table.get(keys[2]), "updated")
        self.assertCountEqual(
            table.items(),
            ((keys[0], "value-0"), (keys[2], "updated")),
        )

    def test_full_table_rejects_new_key_but_allows_existing_key_update(self):
        table = LinearProbingHashTable(capacity=3, max_load=None)
        keys = []
        for bucket_index in range(3):
            key = _keys_for_bucket(table, bucket_index, 1)[0]
            keys.append(key)
            table.put(key, f"value-{bucket_index}")

        self.assertEqual(table.capacity, 3)
        self.assertEqual(table.load_factor, 1.0)
        self.assertIsNone(table.get("not-present"))
        with self.assertRaises(OverflowError):
            table.put("not-present", "overflow")

        table.put(keys[0], "updated")
        self.assertEqual(table.get(keys[0]), "updated")


if __name__ == "__main__":
    unittest.main()
