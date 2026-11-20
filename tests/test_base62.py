import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_zero_is_encoded_as_zero(self):
        self.assertEqual(encode(0), "0")

    def test_alphabet_boundaries(self):
        self.assertEqual(encode(9), "9")
        self.assertEqual(encode(10), "a")
        self.assertEqual(encode(35), "z")
        self.assertEqual(encode(36), "A")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_round_trip(self):
        for number in (1, 62, 3844, 2**128):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_rejects_negative_and_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        with self.assertRaises(TypeError):
            encode("1")
        with self.assertRaises(TypeError):
            encode(True)

    def test_rejects_empty_and_invalid_codes(self):
        for code in ("", "!", "1-", "é"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)
        with self.assertRaises(TypeError):
            decode(1)


if __name__ == "__main__":
    unittest.main()
