# 연봉 실수령액 계산기 (프로그래매틱 SEO 데모)

## 구조
- `calc.py` — 4대보험/소득세 계산 로직 (2026년 요율. 요율은 1월, 국민연금 상·하한은 7월에 갱신 —
  `RATES_YEAR`, `PREVIOUS_YEAR_RATES`도 함께 바꿀 것. 실시간 계산기 JS 요율은 여기서 자동 주입됨)
- `static_pages.py` — about/privacy/contact 페이지 + 공통 SEO 태그 `seo_meta()` (SITE_NAME, CONTACT_EMAIL 여기서 수정)
- `generate.py` — 연봉 구간별 실수령액 페이지(프리셋) + 실시간 입력 계산기가 있는 index.html 생성
- `income_percentile.py` — 연봉 순위(상위 몇 %) 추정 테이블. 국세청이 매년 12월 말 새 백분위 자료를
  공개하므로 그때 앵커 포인트(50/30/10/1%)를 갱신하고 나머지 구간을 재보간할 것
- `generate_severance.py` — 퇴직금 계산기 (입사일·퇴사일 기반)
- `generate_unemployment.py` — 실업급여(구직급여) 계산기 (2026년 상한액 68,100원/하한액 66,048원 기준, 매년 갱신 필요)
- `dividend_data.py` / `generate_dividend.py` — 배당금 계산기 (7개 대형주 2025년 확정 DPS 기준, 결산 시즌마다 갱신 필요)
- `build.py` — 위 모든 generate 스크립트 + sitemap.xml·robots.txt·ads.txt·IndexNow 키 파일을 한 번에 빌드 (실제로는 이걸 실행).
  sitemap의 lastmod는 `lastmod.json`(페이지 내용 해시)으로 실제 내용이 바뀐 페이지만 갱신됨 — 이 파일도 커밋할 것
- `indexnow.py` — 배포 후 네이버·빙에 색인 요청 (구글은 서치콘솔에서 따로)
- `docs/` — 생성된 정적 사이트 (GitHub Pages가 이 폴더를 그대로 서빙함)

## 로컬에서 다시 생성하기
```bash
python build.py
```
배포(push) 후 1~2분 기다렸다가 `python indexnow.py`로 네이버·빙에 변경 사항을 알림.
`generate.py` 상단의 `START`/`END`/`STEP`을 바꾸면 연봉 페이지 개수가 조절됩니다
(예: STEP을 100_000으로 줄이면 페이지가 8배로 늘어남).

## (제거됨) 성과급 계산기
삼성전자·SK하이닉스 성과급(OPI·TAI, PS·PI, 특별경영성과급) 계산기는 2026-08-22 데이터 정확도 문제로
사이트에서 제거했습니다 (`generate_bonus.py`, `generate_special_bonus.py`, `bonus_data.py` 삭제됨).
다시 만들 경우, 사업부별/시점별로 언론사마다 수치가 크게 엇갈리는 문제가 있었으니 단일 공식 출처
(사내 공지, DART 등)로 교차검증하거나 사용자 입력 기반으로 설계할 것.

## 배당금 계산기 데이터 갱신
`dividend_data.py`의 DPS(주당배당금)는 각 회사 결산배당이 확정되는 매년 1~2월경 최신 공시(DART)로
갱신해야 합니다. 배당수익률은 주가 변동 때문에 고정값으로 넣지 않고 사용자가 매수단가를 입력하면
계산되도록 설계되어 있음 — 이 방식을 유지할 것 (특정 시점 주가를 하드코딩하면 곧 부정확해짐).

## 배포 전 반드시 할 일
1. `generate.py`의 `BASE_URL`을 실제 구매한 도메인으로 교체
2. `static_pages.py`의 `CONTACT_EMAIL`을 실제 연락처로 교체
3. `calc.py`의 4대보험 요율/상한액을 최신 공식 고시 수치로 검증
4. 도메인 구매 (가비아, 카페24, Namecheap 등 — 연 1~2만원대)

## 배포 방법 (GitHub Pages, 무료 · Node.js 불필요)
GitHub 계정 생성/로그인, 저장소 생성은 본인이 직접 해야 합니다 (브라우저 인증 필요).

1. https://github.com/new 에서 새 저장소 생성 (Public, README 추가 안 함)
2. 로컬에서 저장소 연결 후 push:
   ```bash
   git remote add origin https://github.com/<내계정>/<저장소명>.git
   git branch -M main
   git push -u origin main
   ```
3. 저장소 → Settings → Pages → **Source: Deploy from a branch**,
   **Branch: main / docs** 선택 → Save
4. 1~2분 후 `https://<내계정>.github.io/<저장소명>/` 로 접속 가능

### 계정명 안 보이게 하려면 (커스텀 도메인 연결)
1. 도메인 구매 (가비아/카페24/Namecheap 등)
2. 저장소 → Settings → Pages → **Custom domain**에 구매한 도메인 입력
   → `docs/CNAME` 파일이 자동 생성됨
3. 도메인 등록업체 DNS 설정에서 A레코드를 GitHub Pages IP로 연결
   (185.199.108.153 / .109.153 / .110.153 / .111.153) 또는 www는 CNAME으로
   `<내계정>.github.io` 연결
4. DNS 전파(최대 몇 시간) 후 Pages 설정에서 **Enforce HTTPS** 체크

### 참고: Vercel을 쓰고 싶다면
동일하게 무료지만 Node.js 설치가 필요합니다 (`npm i -g vercel` → `cd docs && vercel --prod`).

## 검색엔진 등록
1. [Google Search Console](https://search.google.com/search-console) — 도메인 소유권 확인 후 `sitemap.xml` 제출
2. [네이버 서치어드바이저](https://searchadvisor.naver.com) — 동일하게 사이트 등록 + sitemap 제출

## 애드센스 신청 전 체크리스트
- [ ] 실제 도메인 연결 완료
- [ ] 검색엔진에 색인 시작 (제출 후 1~2주 소요)
- [ ] privacy/about/contact 페이지 정상 작동 확인
- [ ] 최소 2~4주 실 방문자 데이터 축적 권장
- [ ] https://www.google.com/adsense 에서 사이트 등록 후 심사 신청
