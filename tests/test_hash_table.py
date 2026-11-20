import unittest

from src.hash_table import HashTable


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


if __name__ == "__main__":
    unittest.main()
