"""
IndexNow로 네이버·빙(및 Yandex 등 참여 검색엔진)에 "이 페이지 새로 생겼거나 바뀌었으니 가져가라"고 알림.
구글은 IndexNow를 지원하지 않으므로 구글은 서치콘솔(사이트맵 제출 / URL 검사 → 색인 생성 요청)로 따로 처리.

사용법: 사이트를 수정해 push한 뒤, GitHub Pages 반영(1~2분)을 기다렸다가 실행
    python indexnow.py                              # sitemap.xml의 전체 URL
    python indexnow.py index.html severance.html    # 일부 페이지만

키 파일(docs/<INDEXNOW_KEY>.txt)이 라이브 사이트에 올라가 있어야 요청이 인정됨.
"""
import sys
import json
import re
import urllib.request
import urllib.error
from build import INDEXNOW_KEY, OUTPUT_DIR
from static_pages import BASE_URL, page_url

ENDPOINTS = [
    "https://searchadvisor.naver.com/indexnow",  # 네이버
    "https://api.indexnow.org/indexnow",         # 빙 등 나머지 참여 검색엔진에 공유됨
]


def sitemap_urls():
    with open(f"{OUTPUT_DIR}/sitemap.xml", encoding="utf-8") as f:
        return re.findall(r"<loc>([^<]+)</loc>", f.read())


def main(files):
    urls = [page_url(f) for f in files] if files else sitemap_urls()
    payload = json.dumps({
        "host": BASE_URL.removeprefix("https://"),
        "key": INDEXNOW_KEY,
        "keyLocation": f"{BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": urls,
    }).encode("utf-8")

    for endpoint in ENDPOINTS:
        req = urllib.request.Request(
            endpoint, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"{endpoint} -> {resp.status} ({len(urls)}개 URL)")  # 200/202면 접수됨
        except urllib.error.HTTPError as e:
            print(f"{endpoint} -> {e.code} {e.read().decode('utf-8', 'replace')[:200]}")


if __name__ == "__main__":
    main(sys.argv[1:])
