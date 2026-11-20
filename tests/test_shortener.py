import unittest

from src.shortener import URLShortener

TABLE_STRATEGIES = ("chaining", "linear")


class URLShortenerTests(unittest.TestCase):
    def test_first_code_is_zero_and_url_round_trips(self):
        url = "https://example.com/path?query=value"

        for strategy in TABLE_STRATEGIES:
            with self.subTest(strategy=strategy):
                shortener = URLShortener(strategy=strategy)

                code = shortener.shorten(url)

                self.assertEqual(code, "0")
                self.assertEqual(shortener.expand(code), url)

    def test_repeated_url_reuses_code_and_different_urls_get_different_codes(self):
        first_url = "https://example.com/first"
        second_url = "https://example.com/second"

        for strategy in TABLE_STRATEGIES:
            with self.subTest(strategy=strategy):
                shortener = URLShortener(strategy=strategy)
                first_code = shortener.shorten(first_url)

                self.assertEqual(shortener.shorten(first_url), first_code)
                self.assertNotEqual(shortener.shorten(second_url), first_code)

    def test_rejects_invalid_urls(self):
        invalid_urls = (
            "",
            " https://example.com",
            "https://example.com ",
            "ftp://example.com",
            "https://",
        )

        for strategy in TABLE_STRATEGIES:
            shortener = URLShortener(strategy=strategy)
            for url in invalid_urls:
                with self.subTest(strategy=strategy, url=url):
                    with self.assertRaises(ValueError):
                        shortener.shorten(url)

    def test_unknown_code_raises_key_error(self):
        for strategy in TABLE_STRATEGIES:
            with self.subTest(strategy=strategy):
                shortener = URLShortener(strategy=strategy)

                with self.assertRaises(KeyError):
                    shortener.expand("Z")

    def test_rejects_unknown_table_strategy(self):
        with self.assertRaises(ValueError):
            URLShortener(strategy="unknown")


if __name__ == "__main__":
    unittest.main()
