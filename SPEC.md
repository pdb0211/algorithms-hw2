# 명세: URL 단축기

## 1. 무엇을 만드는가

사용자가 유효한 HTTP(S) URL을 입력하면 짧은 코드를 받고, 그 코드로 원래 URL을 조회하는
URL 단축기다. 해시 테이블 두 종류를 직접 구현해 같은 인터페이스와 입력으로 동작·탐색
비용을 비교한다.

## 2. base62 인코딩

`src/base62.py`는 `encode(number: int) -> str`와 `decode(code: str) -> int`를 제공한다.
알파벳 순서는 `0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`다.
0은 `"0"`으로 인코딩한다. 음수와 잘못된 입력은 예외로 거부한다. 코드는 비어 있을 수
없고, 알파벳 밖의 문자를 포함할 수 없다.

## 3. 해시 테이블

`src/hash_table.py`의 `HashTable`은 별도 체이닝, `LinearProbingHashTable`은 선형 탐지를
사용한다. 두 클래스 모두 `put(key, value)`, `get(key)`, `remove(key)`, `items()`를
제공하고 키와 값은 문자열이다. 없는 키의 `get`은 `None`, `remove`는 `False`를 반환한다.
검색 후 `last_probes`에 비교한 항목/칸 수를 기록한다. `capacity`는 양의 정수이며,
기본값은 11이다. 기본 모드에서는 체이닝 적재율이 0.75를 넘거나 선형 탐지 적재율이
0.70을 넘으면 용량을 늘리고 재배치한다. 실험은 `auto_resize=False`로 고정 크기를
사용한다. 선형 탐지 테이블이 가득 찬 상태에서 새 키를 넣으면 `OverflowError`를 낸다.

문자열 해시는 `src/hash_table.py`에 직접 구현한 Horner 다항식 해시를 쓴다.
각 문자에 대해 `h = (h * 257 + ord(character)) % capacity`를 계산한다. 충돌 해결은
체이닝 또는 다음 칸으로의 순환 탐색이다. `dict`, `set`, `hash()` 내장 함수는 `src/`
구현에서 사용하지 않는다. 디버깅용 `hash_steps(key)`와 `slots()`는 해시 계산 과정 및
테이블 배치를 조회할 수 있게 한다.

## 4. 단축기

`src/shortener.py`의 `URLShortener.shorten(url)`은 첫 입력이면 짧은 코드를, 같은 URL을
다시 입력하면 기존 코드를 돌려준다. 코드는 순차 ID를 base62로 인코딩한다. 해시값은
코드 생성에 쓰지 않는다. `expand(code)`는 원래 URL을 돌려주고, 없는 코드는
`KeyError`로 거부한다. URL은 앞뒤 공백이 없고 `http` 또는 `https` 스킴과 호스트가
있어야 한다. 잘못된 URL은 `ValueError`로 거부하며, 유효한 URL 문자열은 정규화하지
않고 그대로 보존한다. 기본 테이블은 체이닝이며, `strategy="linear"`로 선형 탐지를
선택할 수 있다.

## 5. 웹 서버

`make serve`는 `src/server.py`에서 표준 라이브러리만으로 HTTP 서버를 실행한다.
`GET /`은 URL 입력 폼을, `POST /`는 단축 결과를 보여준다. `GET /<code>`는 저장된
URL로 302 리다이렉트하고, 알 수 없는 코드는 404를 돌려준다. `GET /table`은 선택된
테이블의 슬롯, 적재율, 검색 비용과 Horner 해시 계산 근거를 HTML로 보여준다. 기본 포트는
8000이며 `PORT` 환경 변수 또는 `--port` 인자로 바꿀 수 있다.

## 6. 경계 사례

- base62: 0, 알파벳 경계(9/a, z/A, Z/10), 큰 정수 왕복, 음수, 잘못된 타입,
  빈 문자열 및 잘못된 글자
- 해시 테이블: 빈 테이블 조회, 충돌, 덮어쓰기, 삭제, 슬롯 끝에서 처음으로 순환하는
  선형 탐지, 삭제 뒤에도 충돌 키 조회, 가득 찬 테이블 삽입, 자동 확장과 재배치
- 단축기: 같은 URL 중복 입력, 서로 다른 URL, 첫 코드 `"0"`, 잘못된 URL, 없는 코드,
  두 테이블 전략에서 같은 동작
- 웹 서버: 폼, 성공/잘못된 입력 응답, 리다이렉트, 없는 코드 404, `/table` 내용
- 실험: 두 전략에 같은 키와 용량을 사용하고, 체이닝 적재율 0.1–4.0 및 선형 탐지
  0.1–0.9에서 탐색 비교 횟수를 이론값과 함께 표·SVG 그래프로 기록한다.
