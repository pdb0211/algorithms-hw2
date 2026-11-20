"""HTTP interface for the in-memory URL shortener."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, unquote, urlsplit

from src.hash_table import HashTable
from src.shortener import URLShortener

MAX_REQUEST_BYTES = 64 * 1024


def _document(title: str, content: str) -> str:
    return (
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{html.escape(title)}</title>"
        "<style>"
        "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;"
        "padding:0 1rem;line-height:1.5}input[type=url]{box-sizing:border-box;"
        "width:min(100%,42rem);padding:.6rem}button{padding:.6rem 1rem}"
        "code,.chain-node{overflow-wrap:anywhere}.chain-node{display:inline-block;"
        "vertical-align:top;border:1px solid #999;border-radius:.4rem;padding:.7rem;"
        "margin:.25rem;max-width:28rem}details{margin-top:.5rem}table{border-collapse:"
        "collapse;width:100%}th,td{border:1px solid #aaa;padding:.5rem;text-align:left}"
        "th{background:#eee}"
        "</style></head><body>"
        f"{content}</body></html>"
    )


def _render_form(message: str = "", url_value: str = "") -> str:
    notice = f'<p role="alert">{html.escape(message)}</p>' if message else ""
    escaped_url = html.escape(url_value, quote=True)
    content = (
        "<h1>URL 단축기</h1>"
        f"{notice}"
        '<form method="post" action="/">'
        '<label for="url">줄일 URL</label><br>'
        f'<input id="url" name="url" type="url" required value="{escaped_url}">'
        '<button type="submit">줄이기</button></form>'
        '<p><a href="/table">해시 테이블 보기</a></p>'
    )
    return _document("URL 단축기", content)


def _render_result(code: str) -> str:
    short_path = f"/{code}"
    escaped_path = html.escape(short_path, quote=True)
    content = (
        "<h1>단축 링크가 준비됐습니다</h1>"
        f'<p><a id="short-link" href="{escaped_path}">{escaped_path}</a></p>'
        '<p><a href="/">다른 URL 줄이기</a> · <a href="/table">해시 테이블 보기</a></p>'
    )
    return _document("단축 결과", content)


def _render_hash_trace(steps: tuple[tuple[str, int], ...], capacity: int) -> str:
    previous_value = 0
    trace_items = []
    for index, (character, value) in enumerate(steps, start=1):
        escaped_character = html.escape(repr(character))
        trace_items.append(
            f"<li>h{index} = (h{index - 1} * {HashTable.HORNER_MULTIPLIER} "
            f"+ ord({escaped_character}) [{ord(character)}]) mod {capacity} = {value}</li>"
        )
        previous_value = value

    bucket_index = previous_value if steps else 0
    trace = "".join(trace_items) or "<li>빈 문자열의 해시값은 0입니다.</li>"
    return (
        "<details><summary>Horner 해시 계산 과정</summary>"
        f"<p>최종 버킷 인덱스: {bucket_index}</p><ol>{trace}</ol></details>"
    )


def _render_table(shortener: URLShortener) -> str:
    capacity, load_factor, buckets = shortener.table_snapshot()
    uses_linear_probing = shortener.strategy == "linear"
    rows = []
    for bucket_index, bucket in enumerate(buckets):
        if not bucket:
            chain = "<em>비어 있음</em>"
        else:
            nodes = []
            for url, code in bucket:
                escaped_url = html.escape(url)
                escaped_code = html.escape(code)
                short_path = f"/{code}"
                escaped_path = html.escape(short_path, quote=True)
                trace = _render_hash_trace(shortener.hash_steps(url), capacity)
                nodes.append(
                    '<section class="chain-node">'
                    f"<div><strong>URL 키:</strong> {escaped_url}</div>"
                    f"<div><strong>짧은 코드:</strong> {escaped_code}</div>"
                    f"<div><strong>저장된 칸:</strong> {bucket_index}</div>"
                    f'<div><strong>짧은 링크:</strong> '
                    f'<a href="{escaped_path}">{escaped_path}</a></div>'
                    f"{trace}</section>"
                )
            if uses_linear_probing:
                chain = nodes[0]
            else:
                chain = " &rarr; ".join(nodes) + " &rarr; None"
        rows.append(f"<tr><th>{bucket_index}</th><td>{chain}</td></tr>")

    strategy_label = "선형 탐지 배열" if uses_linear_probing else "개별 체이닝"
    content = (
        "<h1>현재 해시 테이블</h1>"
        f"<p>충돌 처리 방식: {strategy_label}</p>"
        f"<p>칸 수: {capacity} · 항목 수 적재율: {load_factor:.4f}</p>"
        '<p><a href="/">URL 단축기로 돌아가기</a></p>'
        f"<table><thead><tr><th>칸</th><th>{strategy_label}</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )
    return _document("해시 테이블", content)


def create_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    shortener: URLShortener | None = None,
) -> HTTPServer:
    """Create an HTTP server, optionally using an existing shortener instance."""
    app = shortener if shortener is not None else URLShortener(strategy="linear")

    class ShortenerHandler(BaseHTTPRequestHandler):
        def _send_html(self, status: int, document: str) -> None:
            body = document.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                self._send_html(200, _render_form())
                return
            if path == "/table":
                self._send_html(200, _render_table(app))
                return
            if path.startswith("/") and path.count("/") == 1:
                code = unquote(path[1:])
                try:
                    url = app.expand(code)
                except KeyError:
                    self._send_html(
                        404, _document("링크 없음", "<h1>링크를 찾을 수 없습니다.</h1>")
                    )
                    return
                self.send_response(302)
                self.send_header("Location", url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self._send_html(
                404, _document("페이지 없음", "<h1>페이지를 찾을 수 없습니다.</h1>")
            )

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/":
                self._send_html(
                    404, _document("페이지 없음", "<h1>페이지를 찾을 수 없습니다.</h1>")
                )
                return

            content_length = self.headers.get("Content-Length")
            try:
                body_length = int(content_length) if content_length is not None else -1
            except ValueError:
                body_length = -1
            if body_length < 0:
                self._send_html(400, _render_form("요청 본문 길이가 올바르지 않습니다."))
                return
            if body_length > MAX_REQUEST_BYTES:
                self._send_html(413, _render_form("요청이 너무 큽니다."))
                return

            try:
                form = parse_qsl(
                    self.rfile.read(body_length).decode("utf-8"),
                    keep_blank_values=True,
                    max_num_fields=10,
                )
            except (UnicodeDecodeError, ValueError):
                self._send_html(400, _render_form("요청 내용을 읽을 수 없습니다."))
                return

            url = ""
            for name, value in form:
                if name == "url":
                    url = value
                    break
            try:
                code = app.shorten(url)
            except ValueError as error:
                self._send_html(400, _render_form(str(error), url))
                return
            self._send_html(200, _render_result(code))

    return HTTPServer((host, port), ShortenerHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener HTTP service.")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()
    server = create_server(port=arguments.port)
    print(f"Serving URL shortener on port {arguments.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping URL shortener.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
