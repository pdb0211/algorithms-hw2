import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import create_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server("127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def _request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        response_body = response.read().decode("utf-8")
        return response.status, response.getheader("Location"), response_body

    def test_home_page_has_url_form(self):
        status, _, body = self._request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn('name="url"', body)
        self.assertIn('type="url"', body)

    def test_post_shows_short_link_and_get_redirects(self):
        url = "https://example.com/path"
        payload = urlencode({"url": url}).encode("utf-8")
        status, _, body = self._request(
            "POST",
            "/",
            payload,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

        self.assertEqual(status, 200)
        self.assertIn('href="/0"', body)
        self.assertIn("/0", body)

        status, location, _ = self._request("GET", "/0")
        self.assertEqual(status, 302)
        self.assertEqual(location, url)

    def test_table_page_shows_linear_slots_and_hash_details(self):
        payload = urlencode({"url": "https://example.com/path"}).encode("utf-8")
        self._request(
            "POST",
            "/",
            payload,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

        status, _, body = self._request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn("선형 탐지 배열", body)
        self.assertIn("URL 키", body)
        self.assertIn("짧은 코드", body)
        self.assertIn('href="/0"', body)
        self.assertIn("<details>", body)
        self.assertIn("Horner 해시 계산 과정", body)
        self.assertNotIn("&rarr; None", body)

    def test_invalid_input_and_unknown_code_return_errors(self):
        payload = urlencode({"url": "not-a-url"}).encode("utf-8")
        status, _, _ = self._request(
            "POST",
            "/",
            payload,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 400)

        status, _, _ = self._request("GET", "/missing")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
