"""
전체 사이트 빌드: 모든 계산기 페이지 + sitemap.xml + robots.txt + ads.txt + IndexNow 키 파일
사이트에 계산기를 새로 추가할 때마다 이 파일에 generate 모듈을 import해서 main()을 호출하면 됨.

주의: 삼성전자/SK하이닉스 성과급 계산기는 데이터 정확도 문제로 2026-08-22 제거함
(generate_bonus.py, generate_special_bonus.py, bonus_data.py 삭제됨).
"""
import os
import json
import hashlib
import datetime
import generate
import generate_severance
import generate_unemployment
import generate_dividend
from static_pages import ADSENSE_CLIENT, page_url

OUTPUT_DIR = generate.OUTPUT_DIR
BASE_URL = generate.BASE_URL

# IndexNow(네이버·빙 등) 색인 요청용 키. docs/<키>.txt로 공개돼 있어야 indexnow.py 요청이 인정됨
INDEXNOW_KEY = "87438e6ada502b04300f67a33df322e3"

# 페이지 내용이 실제로 바뀐 날짜 추적용 (docs 밖에 둬서 사이트에는 공개 안 됨)
LASTMOD_MANIFEST = "lastmod.json"


def build_ads_txt():
    pub_id = ADSENSE_CLIENT.replace("ca-pub-", "pub-")
    content = f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n"
    with open(os.path.join(OUTPUT_DIR, "ads.txt"), "w", encoding="utf-8") as f:
        f.write(content)
    print("ads.txt 생성 완료")


def build_robots_txt():
    content = f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n"
    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(content)
    print("robots.txt 생성 완료")


def build_indexnow_key():
    with open(os.path.join(OUTPUT_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def build_sitemap():
    # lastmod는 내용(해시)이 바뀐 페이지만 오늘 날짜로 갱신.
    # 빌드할 때마다 전부 오늘 날짜로 찍으면 검색엔진이 lastmod 자체를 무시하게 됨
    try:
        with open(LASTMOD_MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        manifest = {}
    today = datetime.date.today().isoformat()

    new_manifest = {}
    entries = []
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if not fname.endswith(".html"):
            continue
        with open(os.path.join(OUTPUT_DIR, fname), "rb") as f:
            digest = hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()
        prev = manifest.get(fname)
        lastmod = prev["lastmod"] if prev and prev["sha256"] == digest else today
        new_manifest[fname] = {"sha256": digest, "lastmod": lastmod}
        entries.append(f"  <url><loc>{page_url(fname)}</loc><lastmod>{lastmod}</lastmod></url>")

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(entries)}
</urlset>"""
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)
    with open(LASTMOD_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(new_manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"sitemap.xml 갱신 완료 ({len(entries)}개 URL)")


def main():
    generate.main()
    generate_severance.main()
    generate_unemployment.main()
    generate_dividend.main()
    build_ads_txt()
    build_robots_txt()
    build_indexnow_key()
    build_sitemap()


if __name__ == "__main__":
    main()
