"""
애드센스 심사에 필요한 필수 정적 페이지 (개인정보처리방침 / 사이트소개)
(문의 페이지는 개인 연락처 노출을 피하려고 2026-09-22 제거함)
+ 모든 페이지 <head>에 공통으로 들어가는 SEO 태그(canonical, Open Graph, 구조화 데이터)
"""
import html
import json

SITE_NAME = "연봉실수령액계산기"
BASE_URL = "https://krcalctools.github.io"

ADSENSE_CLIENT = "ca-pub-5607384951754093"


def page_url(filename):
    """홈은 /index.html 대신 루트 URL로 통일 (중복 URL 방지)"""
    return f"{BASE_URL}/" if filename == "index.html" else f"{BASE_URL}/{filename}"


def seo_meta(filename, title, desc, app_name=None):
    """canonical + Open Graph(카톡·커뮤니티 링크 미리보기) 태그. app_name을 주면 계산기용 구조화 데이터도 추가"""
    url = page_url(filename)
    t, d = html.escape(title), html.escape(desc)
    tags = f"""<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ko_KR">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">"""
    if app_name:
        ld = {
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": app_name,
            "url": url,
            "description": desc,
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "All",
            "inLanguage": "ko",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "KRW"},
        }
        tags += f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    return tags

GA_SNIPPET = f"""<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-HKGC6LX6C4"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-HKGC6LX6C4');
</script>
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}"
     crossorigin="anonymous"></script>"""

FOOTER_NAV = """
  <div class="footer-nav">
    <a href="index.html">연봉 실수령액</a>
    <a href="salary-table.html">연봉 실수령액표</a>
    <a href="severance.html">퇴직금 계산기</a>
    <a href="unemployment.html">실업급여 계산기</a>
    <a href="dividend.html">배당금 계산기</a>
    <a href="about.html">사이트 소개</a>
    <a href="privacy.html">개인정보처리방침</a>
  </div>
"""

FAVICON = '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27%3E%3Ctext y=%27.9em%27 font-size=%2790%27%3E%F0%9F%A7%AE%3C/text%3E%3C/svg%3E">'

SITE_HEADER = """
  <header class="site-header">
    <a href="index.html" class="brand">🧮 머니계산기</a>
    <nav class="site-nav">
      <a href="index.html">연봉</a>
      <a href="salary-table.html">실수령액표</a>
      <a href="severance.html">퇴직금</a>
      <a href="unemployment.html">실업급여</a>
      <a href="dividend.html">배당금</a>
    </nav>
  </header>
"""

SITE_STYLE = """
  :root {
    --primary: #2563eb; --primary-dark: #1d4ed8; --bg: #f8f9fc; --card-bg: #ffffff;
    --text: #111827; --muted: #6b7280; --border: #e5e7eb;
    --warn-bg: #fff7ed; --warn-text: #9a3412;
  }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Malgun Gothic", sans-serif;
    max-width: 680px; margin: 0 auto; padding: 0 20px 60px; color: var(--text);
    line-height: 1.7; background: var(--bg);
  }
  a { color: var(--primary); }
  .site-header {
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
    gap: 10px; padding: 18px 0; border-bottom: 1px solid var(--border); margin-bottom: 28px;
  }
  .site-header .brand { font-weight: 800; font-size: 17px; color: var(--text); text-decoration: none; }
  .site-nav { display: flex; gap: 2px; flex-wrap: wrap; }
  .site-nav a { font-size: 13px; color: var(--muted); text-decoration: none; padding: 6px 10px; border-radius: 999px; }
  .site-nav a:hover { background: #eef2ff; color: var(--primary); }

  h1 { font-size: 23px; margin-bottom: 8px; }
  h2 { font-size: 16px; margin-top: 28px; }

  .calc-box {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px;
    padding: 22px; margin: 20px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .field { margin-bottom: 14px; }
  .field label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 5px; font-weight: 500; }
  .field input, .field select {
    width: 100%; box-sizing: border-box; padding: 11px 13px; font-size: 16px;
    border: 1px solid var(--border); border-radius: 10px; background: #fff;
  }
  .field input:focus, .field select:focus { outline: 2px solid var(--primary); border-color: var(--primary); }
  .field.checkbox { display: flex; align-items: center; gap: 8px; }
  .field.checkbox label { margin-bottom: 0; }
  .date-select-row { display: flex; gap: 6px; }
  .date-select-row select { flex: 1; min-width: 0; }

  .result { margin-top: 18px; padding-top: 16px; border-top: 1px dashed var(--border); }
  .result-row { display: flex; justify-content: space-between; padding: 7px 0; font-size: 14px; }
  .result-row.total {
    font-weight: 800; font-size: 19px; color: var(--primary);
    border-top: 1px solid var(--border); margin-top: 8px; padding-top: 12px;
  }

  .headline {
    background: linear-gradient(135deg,#eef2ff,#f5f3ff); border-radius: 16px;
    padding: 26px; text-align: center; margin: 20px 0;
  }
  .headline .amount { font-size: 34px; font-weight: 800; color: var(--primary); }

  .percentile-badge {
    margin: 16px 0; padding: 14px 16px; background: #fef9e7; border: 1px solid #fde68a;
    border-radius: 10px; font-size: 14px; color: #78350f;
  }
  .percentile-badge b { color: #92400e; }
  .percentile-source { display: block; margin-top: 4px; font-size: 11px; color: #a16207; }

  .donut-wrap { display: flex; align-items: center; justify-content: center; gap: 24px; flex-wrap: wrap; margin: 20px 0; }
  .donut-chart {
    width: 140px; height: 140px; border-radius: 50%; flex-shrink: 0;
    background: conic-gradient(var(--primary) calc(var(--pct) * 1%), #e5e7eb 0);
    display: flex; align-items: center; justify-content: center;
  }
  .donut-center {
    width: 100px; height: 100px; border-radius: 50%; background: var(--card-bg);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
  }
  .donut-pct { font-size: 22px; font-weight: 800; color: var(--primary); }
  .donut-label { font-size: 11px; color: var(--muted); }
  .donut-legend { font-size: 13px; }
  .donut-legend div { display: flex; align-items: center; gap: 8px; margin: 6px 0; }
  .donut-legend .dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .donut-legend .dot.net { background: var(--primary); }
  .donut-legend .dot.deduction { background: #e5e7eb; }

  .cross-link-box {
    margin: 20px 0; padding: 16px; background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 10px; font-size: 14px;
  }
  .cross-link-box a { font-weight: 600; }

  table.rule, table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 13px; }
  table.rule th, table.rule td, table th, table td { border: 1px solid var(--border); padding: 9px 10px; text-align: left; }
  table.rule td.num, table td.num { text-align: right; }
  th { color: var(--muted); font-weight: 600; background: #fafafa; }
  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  table.compact { font-size: 12px; }
  table.compact th, table.compact td { padding: 7px 6px; }
  table.compact td { white-space: nowrap; }
  @media (max-width: 400px) { .site-nav a { padding: 6px 7px; } }

  .pending { color: #b45309; font-size: 12px; }
  .warning { margin-top: 12px; padding: 10px 12px; background: var(--warn-bg); border-radius: 10px; font-size: 13px; color: var(--warn-text); display: none; }
  .stock-note { font-size: 12px; color: var(--muted); margin-top: 8px; }

  .source { font-size: 12px; color: var(--muted); }
  .source a { color: var(--muted); }
  .disclaimer {
    margin-top: 32px; padding: 14px 16px; background: #fafafa; border-radius: 10px;
    font-size: 12px; color: var(--muted); line-height: 1.6;
  }

  .explain { margin-top: 26px; font-size: 14px; color: #374151; }
  .explain h2 { font-size: 15px; }
  .steps { margin: 12px 0 0; padding-left: 20px; }
  .steps li { margin-bottom: 8px; }
  .steps .num { color: var(--primary); font-weight: 700; }

  .nav { margin-top: 24px; font-size: 14px; }
  .nav a { text-decoration: none; }

  .division-list { list-style: none; padding: 0; margin: 18px 0; display: grid; gap: 8px; }
  .division-list li a {
    display: block; padding: 12px 16px; background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 10px; text-decoration: none; color: var(--text); font-size: 14px;
  }
  .division-list li a:hover { border-color: var(--primary); color: var(--primary); }

  .footer-nav {
    margin-top: 40px; padding-top: 18px; border-top: 1px solid var(--border);
    font-size: 13px; color: var(--muted); display: flex; flex-wrap: wrap; gap: 4px 14px;
  }
  .footer-nav a { color: var(--muted); text-decoration: none; }
  .footer-nav a:hover { color: var(--primary); }
"""


def about_html():
    return f"""<!doctype html>
<html lang="ko">
<head>
{GA_SNIPPET}
<meta charset="utf-8">
<title>사이트 소개 - {SITE_NAME}</title>
<meta name="description" content="{SITE_NAME}의 계산 방식과 기준을 안내합니다.">
{seo_meta("about.html", f"사이트 소개 - {SITE_NAME}", f"{SITE_NAME}의 계산 방식과 기준을 안내합니다.")}
<meta name="viewport" content="width=device-width, initial-scale=1">
{FAVICON}
<style>{SITE_STYLE}</style>
</head>
<body>
{SITE_HEADER}
  <h1>사이트 소개</h1>
  <p>{SITE_NAME}는 연봉 구간별 4대보험(국민연금·건강보험·장기요양보험·고용보험)과 소득세 공제 내역을
  계산해 예상 월 실수령액을 안내하는 사이트입니다.</p>

  <h2>계산 방식</h2>
  <p>1인 가구, 기본공제만 적용한 단순화된 모델을 기준으로 계산합니다. 부양가족 수, 각종 세액공제,
  비과세 수당 등 개인별 상황에 따라 실제 원천징수 금액과 차이가 있을 수 있습니다. 4대보험 요율은
  매년 변경되므로 사이트 운영자가 주기적으로 최신 고시 수치를 반영하여 갱신합니다.</p>

  <h2>정확한 금액이 필요하다면</h2>
  <p>정확한 원천징수 세액은 국세청 홈택스 또는 재직 중인 회사의 급여 담당 부서를 통해 확인하시기
  바랍니다. 본 사이트의 계산 결과는 참고용 추정치입니다.</p>

{FOOTER_NAV}
</body>
</html>"""


def privacy_html():
    return f"""<!doctype html>
<html lang="ko">
<head>
{GA_SNIPPET}
<meta charset="utf-8">
<title>개인정보처리방침 - {SITE_NAME}</title>
{seo_meta("privacy.html", f"개인정보처리방침 - {SITE_NAME}", f"{SITE_NAME} 개인정보처리방침")}
<meta name="viewport" content="width=device-width, initial-scale=1">
{FAVICON}
<style>{SITE_STYLE}</style>
</head>
<body>
{SITE_HEADER}
  <h1>개인정보처리방침</h1>
  <p>{SITE_NAME}(이하 '사이트')는 이용자의 개인정보를 소중히 다루며, 다음과 같이 개인정보처리방침을
  안내드립니다.</p>

  <h2>1. 수집하는 개인정보 항목</h2>
  <p>본 사이트는 회원가입이나 로그인 기능이 없으며, 이용자가 직접 입력하는 개인정보를 수집하지
  않습니다. 다만 광고 게재 및 서비스 개선을 위해 Google AdSense, Google Analytics 등 제3자
  서비스를 통해 쿠키 기반의 방문 기록(방문 페이지, 접속 기기, 대략적 위치 등)이 자동 수집될 수
  있습니다.</p>

  <h2>2. 쿠키(Cookie)의 사용</h2>
  <p>본 사이트는 광고 게재를 위해 Google 및 협력사의 쿠키를 사용합니다. 이용자는 브라우저 설정을
  통해 쿠키 저장을 거부할 수 있으며, Google 광고 개인 최적화 설정은
  <a href="https://adssettings.google.com" target="_blank" rel="noopener">Google 광고 설정</a>
  페이지에서 변경할 수 있습니다.</p>

  <h2>3. 제3자 광고 서비스</h2>
  <p>본 사이트는 Google AdSense를 통해 광고를 게재하며, Google은 이용자의 관심사에 기반한 광고를
  제공하기 위해 쿠키를 사용할 수 있습니다. 자세한 내용은 Google의 광고 정책을 참고하시기 바랍니다.</p>

  <h2>4. 시행일</h2>
  <p>본 방침은 2026년 9월 22일부터 적용됩니다.</p>

{FOOTER_NAV}
</body>
</html>"""
