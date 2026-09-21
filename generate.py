"""
연봉 실수령액 페이지 대량 생성 스크립트 (프로그래매틱 SEO 예시)

START_LOW/BOUNDARY/END/STEP_LOW/STEP_HIGH 만 조절하면 페이지 수/구간이 그대로 바뀐다.
각 페이지는 독립된 정적 HTML이라 호스팅 비용이 거의 안 들고(Vercel/Netlify 무료 티어),
검색엔진이 각각을 별도 URL로 색인한다.
"""
import os
import json
import calc
from calc import calculate, RATES_YEAR
from income_percentile import estimate_top_percent, PERCENTILE_TABLE, SOURCE_NOTE as PERCENTILE_SOURCE_NOTE
from static_pages import about_html, privacy_html, contact_html, SITE_NAME, GA_SNIPPET, FOOTER_NAV, SITE_STYLE, SITE_HEADER, FAVICON, BASE_URL, seo_meta

PERCENTILE_TABLE_JS = f"const PERCENTILE_TABLE = {json.dumps(PERCENTILE_TABLE)};\n"

OUTPUT_DIR = "docs"  # GitHub Pages가 /docs 폴더를 바로 서빙할 수 있어서 이 이름 사용

START_LOW = 30_000_000     # 3,000만원
BOUNDARY = 100_000_000     # 1억원 - 이 지점부터 STEP_HIGH로 전환
END = 150_000_000          # 1억 5,000만원
STEP_LOW = 1_000_000       # 1억 미만: 100만원 단위 (실제 검색 패턴에 맞춤)
STEP_HIGH = 10_000_000     # 1억 이상: 1,000만원 단위 (고연봉 구간은 더 성기게)


def build_salaries():
    low = list(range(START_LOW, BOUNDARY, STEP_LOW))
    high = list(range(BOUNDARY, END + 1, STEP_HIGH))
    return low + high


# 요율 상수는 calc.py에서 주입 → 프리셋 페이지(Python)와 실시간 계산기(JS) 요율이 어긋나지 않음
SALARY_CALC_JS = f"""
const PENSION_RATE = {calc.PENSION_RATE}, PENSION_CAP = {calc.PENSION_CAP_MONTHLY}, PENSION_FLOOR = {calc.PENSION_FLOOR_MONTHLY};
const HEALTH_RATE = {calc.HEALTH_RATE}, LTC_RATE_OF_HEALTH = {calc.LONGTERM_CARE_RATE_OF_HEALTH}, EMPLOYMENT_RATE = {calc.EMPLOYMENT_RATE};
const EARNED_INCOME_DEDUCTION_CAP = {calc.EARNED_INCOME_DEDUCTION_CAP};
""" + """
function earnedIncomeDeduction(g) {
  if (g <= 5000000) return g * 0.7;
  if (g <= 15000000) return 3500000 + (g - 5000000) * 0.4;
  if (g <= 45000000) return 7500000 + (g - 15000000) * 0.15;
  if (g <= 100000000) return 12000000 + (g - 45000000) * 0.05;
  return Math.min(14750000 + (g - 100000000) * 0.02, EARNED_INCOME_DEDUCTION_CAP);
}

const TAX_BRACKETS = [
  [12000000, 0.06, 0], [46000000, 0.15, 1080000], [88000000, 0.24, 5220000],
  [150000000, 0.35, 14900000], [300000000, 0.38, 19400000], [500000000, 0.40, 25400000],
  [1000000000, 0.42, 35400000], [Infinity, 0.45, 65400000],
];

function taxByBracket(base) {
  if (base <= 0) return 0;
  for (const [limit, rate, deduction] of TAX_BRACKETS) {
    if (base <= limit) return base * rate - deduction;
  }
  return 0;
}

function earnedIncomeTaxCredit(tax, annual) {
  let credit = tax <= 1300000 ? tax * 0.55 : 715000 + (tax - 1300000) * 0.3;
  let cap;
  if (annual <= 33000000) cap = 740000;
  else if (annual <= 70000000) cap = Math.max(660000, 740000 - (annual - 33000000) * 0.008);
  else if (annual <= 120000000) cap = Math.max(500000, 660000 - (annual - 70000000) * 0.5);
  else cap = Math.max(200000, 500000 - (annual - 120000000) * 0.5);
  return Math.min(credit, cap);
}

function calculateSalary(annual) {
  const monthly = annual / 12;
  const pensionBase = Math.min(Math.max(monthly, PENSION_FLOOR), PENSION_CAP);
  const pension = Math.round(pensionBase * PENSION_RATE);
  const health = Math.round(monthly * HEALTH_RATE);
  const ltc = Math.round(health * LTC_RATE_OF_HEALTH);
  const employment = Math.round(monthly * EMPLOYMENT_RATE);

  const deduction = earnedIncomeDeduction(annual);
  const earnedIncomeAmount = Math.max(annual - deduction, 0);
  const comprehensiveDeduction = 1500000 + pension * 12 + (health + ltc) * 12;
  const taxableBase = Math.max(earnedIncomeAmount - comprehensiveDeduction, 0);
  const calculatedTax = taxByBracket(taxableBase);
  const credit = earnedIncomeTaxCredit(calculatedTax, annual);
  const finalTaxAnnual = Math.max(calculatedTax - credit, 0);

  const incomeTax = Math.round(finalTaxAnnual / 12);
  const localTax = Math.round(incomeTax * 0.1);
  const totalDeduction = pension + health + ltc + employment + incomeTax + localTax;
  const netMonthly = Math.round(monthly - totalDeduction);

  return { pension, health, ltc, employment, incomeTax, localTax, netMonthly, totalDeduction, monthly };
}

function calc() {
  const manInput = parseFloat(document.getElementById('annual').value) || 0;
  const annual = manInput * 10000;
  if (annual <= 0) return;
  const r = calculateSalary(annual);
  document.getElementById('pension').textContent = r.pension.toLocaleString() + '원';
  document.getElementById('health').textContent = r.health.toLocaleString() + '원';
  document.getElementById('ltc').textContent = r.ltc.toLocaleString() + '원';
  document.getElementById('employment').textContent = r.employment.toLocaleString() + '원';
  document.getElementById('tax').textContent = (r.incomeTax + r.localTax).toLocaleString() + '원';
  document.getElementById('net').textContent = r.netMonthly.toLocaleString() + '원';

  const topPct = estimateTopPercent(manInput);
  document.getElementById('percentile').textContent = '상위 ' + topPct + '%';
  document.getElementById('percentileBadge').style.display = 'block';

  const netPct = Math.round((r.netMonthly / r.monthly) * 1000) / 10;
  document.getElementById('donutChart').style.setProperty('--pct', netPct);
  document.getElementById('donutPct').textContent = netPct + '%';
  document.getElementById('donutNetLabel').textContent = '실수령액 ' + r.netMonthly.toLocaleString() + '원 (' + netPct + '%)';
  document.getElementById('donutDeductionLabel').textContent = '공제액 ' + r.totalDeduction.toLocaleString() + '원 (' + (Math.round((100 - netPct) * 10) / 10) + '%)';
  document.getElementById('donutWrap').style.display = 'flex';

  const monthlyMan = Math.round(annual / 12 / 10000);
  document.getElementById('severanceLink').href = 'severance.html?monthly=' + monthlyMan;
  document.getElementById('unemploymentLink').href = 'unemployment.html?monthly=' + monthlyMan;
  document.getElementById('crossLinkBox').style.display = 'block';
}

function estimateTopPercent(annualMan) {
  const table = PERCENTILE_TABLE;
  if (annualMan >= table[0][1]) return table[0][0];
  if (annualMan <= table[table.length - 1][1]) return table[table.length - 1][0];
  for (let i = 0; i < table.length - 1; i++) {
    const [pHi, vHi] = table[i];
    const [pLo, vLo] = table[i + 1];
    if (annualMan >= vLo && annualMan <= vHi) {
      const ratio = (annualMan - vLo) / (vHi - vLo);
      return Math.round((pLo - ratio * (pLo - pHi)) * 10) / 10;
    }
  }
  return 90.0;
}
"""


def fmt(n):
    return f"{n:,}"


def fmt_eok(salary_won):
    """1억원 이상은 '1억 500만원' 식으로, 미만은 기존처럼 '만원' 단위로 표기"""
    eok = salary_won // 100_000_000
    man = (salary_won % 100_000_000) // 10_000
    if eok == 0:
        return f"{man:,}만원"
    if man == 0:
        return f"{eok}억원"
    return f"{eok}억 {man:,}만원"


def search_label(salary_won):
    """사람들이 검색창에 실제로 치는 형태 ('연봉 4200 실수령액', '연봉 1억2천 실수령액')"""
    eok = salary_won // 100_000_000
    man = (salary_won % 100_000_000) // 10_000
    if eok == 0:
        return f"{man}"
    if man == 0:
        return f"{eok}억"
    if man % 1000 == 0:
        return f"{eok}억{man // 1000}천"
    return f"{eok}억{man}"


def pct(rate):
    """0.0475 -> '4.75' (부동소수점 꼬리 제거)"""
    return f"{rate * 100:g}"


def slug(salary):
    man = salary // 10_000
    return f"salary-{man}"


def page_html(salary, prev_salary, next_salary):
    r = calculate(salary)
    man = salary // 10_000
    label = fmt_eok(salary)
    top_pct = estimate_top_percent(man)
    net_pct = round(r['net_monthly'] / r['gross_monthly'] * 100, 1)
    monthly_man = round(salary / 12 / 10_000)
    title = f"연봉 {search_label(salary)} 실수령액 - 월 {fmt(r['net_monthly'])}원 ({RATES_YEAR}년 기준)"
    desc = f"{RATES_YEAR}년 4대보험 요율 기준, 연봉 {label}의 세후 실수령액은 월 약 {fmt(r['net_monthly'])}원입니다. 4대보험, 소득세 공제 내역과 소득 순위를 확인하세요."

    nav_links = []
    if prev_salary:
        nav_links.append(f'<a href="{slug(prev_salary)}.html">← 연봉 {fmt_eok(prev_salary)}</a>')
    if next_salary:
        nav_links.append(f'<a href="{slug(next_salary)}.html">연봉 {fmt_eok(next_salary)} →</a>')
    nav_html = " | ".join(nav_links)

    return f"""<!doctype html>
<html lang="ko">
<head>
{GA_SNIPPET}
<meta charset="utf-8">
<title>{title}</title>
<meta name="description" content="{desc}">
{seo_meta(f"{slug(salary)}.html", title, desc)}
<meta name="viewport" content="width=device-width, initial-scale=1">
{FAVICON}
<style>{SITE_STYLE}</style>
</head>
<body>
{SITE_HEADER}
  <h1>연봉 {label} 실수령액 계산 결과</h1>
  <div class="headline">
    <div>세전 연봉 {label}의 월 실수령액</div>
    <div class="amount">{fmt(r['net_monthly'])}원</div>
    <div>연 실수령액 약 {fmt(r['net_annual'])}원</div>
  </div>

  <div class="percentile-badge">
    💡 연봉 {label}은(는) 대한민국 근로소득자 중 <b>상위 {top_pct}%</b>에 해당하는 것으로 추정됩니다.
    <span class="percentile-source">({PERCENTILE_SOURCE_NOTE})</span>
  </div>

  <div class="donut-wrap">
    <div class="donut-chart" style="--pct: {net_pct}">
      <div class="donut-center">
        <div class="donut-pct">{net_pct}%</div>
        <div class="donut-label">실수령 비율</div>
      </div>
    </div>
    <div class="donut-legend">
      <div><span class="dot net"></span>실수령액 {fmt(r['net_monthly'])}원 ({net_pct}%)</div>
      <div><span class="dot deduction"></span>공제액 {fmt(r['total_deduction'])}원 ({round(100 - net_pct, 1)}%)</div>
    </div>
  </div>

  <table>
    <tr><th>항목</th><th>월 공제액</th></tr>
    <tr><td>국민연금</td><td>{fmt(r['pension'])}원</td></tr>
    <tr><td>건강보험</td><td>{fmt(r['health'])}원</td></tr>
    <tr><td>장기요양보험</td><td>{fmt(r['longterm_care'])}원</td></tr>
    <tr><td>고용보험</td><td>{fmt(r['employment'])}원</td></tr>
    <tr><td>소득세</td><td>{fmt(r['income_tax'])}원</td></tr>
    <tr><td>지방소득세</td><td>{fmt(r['local_tax'])}원</td></tr>
    <tr><th>공제 합계</th><th>{fmt(r['total_deduction'])}원</th></tr>
  </table>

  <div class="cross-link-box">
    이 월급여(약 {fmt(monthly_man)}만원) 기준으로 다른 계산도 해보세요:
    <a href="severance.html?monthly={monthly_man}">🔗 퇴직금 계산기</a> ·
    <a href="unemployment.html?monthly={monthly_man}">🔗 실업급여 계산기</a>
  </div>

  <div class="nav">{nav_html}</div>

  <div class="explain">
    <h2>연봉 {label}의 실수령액 계산 과정</h2>
    <ol class="steps">
      <li>월 급여 = 연봉 {label} ÷ 12 = <span class="num">{fmt(r['gross_monthly'])}원</span></li>
      <li>4대보험 공제(월) = 국민연금 {fmt(r['pension'])}원 + 건강보험 {fmt(r['health'])}원
        + 장기요양보험 {fmt(r['longterm_care'])}원 + 고용보험 {fmt(r['employment'])}원
        = <span class="num">{fmt(r['pension'] + r['health'] + r['longterm_care'] + r['employment'])}원</span></li>
      <li>근로소득공제(연) = <span class="num">{fmt(r['earned_income_deduction'])}원</span>을 연봉에서 제외 →
        근로소득금액 <span class="num">{fmt(r['earned_income_amount'])}원</span></li>
      <li>종합소득공제(연) = 기본공제 150만원 + 국민연금 납부액(연) + 건강보험료 납부액(연)
        = <span class="num">{fmt(r['comprehensive_deduction'])}원</span></li>
      <li>과세표준 = 근로소득금액 − 종합소득공제 = <span class="num">{fmt(r['taxable_base'])}원</span></li>
      <li>산출세액(연) = 과세표준에 누진세율 적용 = <span class="num">{fmt(r['calculated_tax_annual'])}원</span></li>
      <li>근로소득세액공제(연) = <span class="num">{fmt(r['tax_credit_annual'])}원</span> 차감 →
        결정세액(연) <span class="num">{fmt(r['final_tax_annual'])}원</span> → 월 소득세
        <span class="num">{fmt(r['income_tax'])}원</span> (+지방소득세 {fmt(r['local_tax'])}원)</li>
      <li>실수령액 = 월급여 − 4대보험 − 소득세 − 지방소득세 = <span class="num">{fmt(r['net_monthly'])}원</span></li>
    </ol>
  </div>

  <div class="explain">
    <h2>공제 항목 설명</h2>
    <p>국민연금은 기준소득월액의 {pct(calc.PENSION_RATE)}%를 근로자가 부담하며, 기준소득월액 상한액({fmt(calc.PENSION_CAP_MONTHLY)}원)과
    하한액({fmt(calc.PENSION_FLOOR_MONTHLY)}원)은 매년 7월 조정됩니다.
    건강보험은 소득의 {pct(calc.HEALTH_RATE)}%, 여기에 건강보험료의 {pct(calc.LONGTERM_CARE_RATE_OF_HEALTH)}%가 장기요양보험료로 추가 부과됩니다.
    고용보험은 소득의 {pct(calc.EMPLOYMENT_RATE)}%이며, 소득세와 지방소득세는 연간 근로소득을 기준으로 누진세율이
    적용된 뒤 12개월로 나눈 값입니다. 부양가족이 있거나 각종 세액공제 대상이라면 실제 공제액은
    이 표보다 낮아질 수 있습니다.</p>
  </div>

  <div class="disclaimer">
    ※ 본 계산은 1인 가구 기준으로 기본공제·연금보험료공제·건강보험료 특별소득공제를 반영한
    추정치입니다. 부양가족 공제, 카드사용액 등 그 외 소득·세액공제, 비과세 수당 등은 반영하지
    않아 실제 금액과 차이가 있을 수 있습니다. 4대보험 요율은 {RATES_YEAR}년 기준(국민연금 상·하한은 {RATES_YEAR}년 7월
    적용분)이며 매년 변경되므로 정확한 금액은 국세청 홈택스 원천징수세액 조회를 참고하세요.
  </div>

{FOOTER_NAV}
</body>
</html>"""


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    salaries = build_salaries()

    # 구간/단위가 바뀌면 예전 값으로 만들어진 salary-*.html이 남을 수 있어 먼저 정리
    valid_filenames = {f"{slug(s)}.html" for s in salaries}
    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith("salary-") and fname.endswith(".html") and fname not in valid_filenames:
            os.remove(os.path.join(OUTPUT_DIR, fname))

    for i, salary in enumerate(salaries):
        prev_s = salaries[i - 1] if i > 0 else None
        next_s = salaries[i + 1] if i < len(salaries) - 1 else None
        html = page_html(salary, prev_s, next_s)
        path = os.path.join(OUTPUT_DIR, f"{slug(salary)}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    # 필수 정적 페이지 (애드센스 심사용)
    static_files = {"about.html": about_html(), "privacy.html": privacy_html(), "contact.html": contact_html()}
    for filename, html in static_files.items():
        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
            f.write(html)

    # index.html - 전체 목록
    links = "\n".join(
        f'<li><a href="{slug(s)}.html">연봉 {fmt_eok(s)} 실수령액</a></li>' for s in salaries
    )
    prev = calc.PREVIOUS_YEAR_RATES
    rate_rows = [
        ("국민연금", prev["pension"], calc.PENSION_RATE),
        ("건강보험", prev["health"], calc.HEALTH_RATE),
        ("장기요양보험 (건강보험료 대비)", prev["longterm_care_of_health"], calc.LONGTERM_CARE_RATE_OF_HEALTH),
        ("고용보험", prev["employment"], calc.EMPLOYMENT_RATE),
    ]
    rate_table = "\n".join(
        f"  <tr><td>{name}</td><td>{pct(old)}%</td><td><b>{pct(new)}%</b></td></tr>"
        for name, old, new in rate_rows
    )
    index_title = f"연봉 실수령액 계산기 {RATES_YEAR} - 4대보험·세금 공제 후 월급 바로 계산"
    index_desc = (f"{RATES_YEAR}년 4대보험 요율(국민연금 {pct(calc.PENSION_RATE)}%, 건강보험 {pct(calc.HEALTH_RATE)}%)을 반영한 "
                  f"연봉 실수령액 계산기. 연봉을 입력하면 월 실수령액, 공제 내역, 소득 상위 %를 바로 계산합니다.")
    index_html = f"""<!doctype html>
<html lang="ko"><head>
{GA_SNIPPET}
<meta charset="utf-8"><title>{index_title}</title>
<meta name="description" content="{index_desc}">
{seo_meta("index.html", index_title, index_desc, app_name="연봉 실수령액 계산기")}
<meta name="google-site-verification" content="22jd1Q9gwpfGcwd0MvSlxlhC8mekAJ9CjNMXHGUHASE" />
<meta name="naver-site-verification" content="2619bf9b6ab4ed06c679f8f24d5b50df019827ac" />
<meta name="viewport" content="width=device-width, initial-scale=1">
{FAVICON}
<style>{SITE_STYLE}</style></head>
<body>
{SITE_HEADER}
<h1>연봉 실수령액 계산기 ({RATES_YEAR}년 기준)</h1>
<p>정확한 연봉을 입력하면 바로 계산됩니다. 아래 목록은 자주 찾는 연봉 구간별 상세 계산 결과입니다.</p>

<div class="calc-box">
  <div class="field">
    <label for="annual">연봉 (세전, 만원)</label>
    <input type="number" id="annual" placeholder="예: 3637" oninput="calc()">
  </div>
  <div class="result">
    <div class="result-row"><span>국민연금</span><span id="pension">-</span></div>
    <div class="result-row"><span>건강보험</span><span id="health">-</span></div>
    <div class="result-row"><span>장기요양보험</span><span id="ltc">-</span></div>
    <div class="result-row"><span>고용보험</span><span id="employment">-</span></div>
    <div class="result-row"><span>소득세+지방소득세</span><span id="tax">-</span></div>
    <div class="result-row total"><span>월 실수령액</span><span id="net">-</span></div>
  </div>
  <div class="percentile-badge" id="percentileBadge" style="display:none">
    💡 이 연봉은 대한민국 근로소득자 중 <b><span id="percentile">-</span></b>에 해당하는 것으로 추정됩니다.
    <span class="percentile-source">({PERCENTILE_SOURCE_NOTE})</span>
  </div>
  <div class="donut-wrap" id="donutWrap" style="display:none">
    <div class="donut-chart" id="donutChart">
      <div class="donut-center">
        <div class="donut-pct" id="donutPct">-</div>
        <div class="donut-label">실수령 비율</div>
      </div>
    </div>
    <div class="donut-legend">
      <div><span class="dot net"></span><span id="donutNetLabel">-</span></div>
      <div><span class="dot deduction"></span><span id="donutDeductionLabel">-</span></div>
    </div>
  </div>
  <div class="cross-link-box" id="crossLinkBox" style="display:none">
    이 월급여 기준으로 다른 계산도 해보세요:
    <a id="severanceLink" href="severance.html">🔗 퇴직금 계산기</a> ·
    <a id="unemploymentLink" href="unemployment.html">🔗 실업급여 계산기</a>
  </div>
</div>

<p><a href="severance.html"><b>퇴직금 계산기</b></a> | <a href="unemployment.html"><b>실업급여 계산기</b></a> | <a href="dividend.html"><b>배당금 계산기</b></a></p>

<h2>{RATES_YEAR}년 달라진 4대보험 요율 (근로자 부담분)</h2>
<table>
  <tr><th>항목</th><th>{prev["year"]}년</th><th>{RATES_YEAR}년</th></tr>
{rate_table}
</table>
<p class="source">국민연금 보험료율은 연금개혁에 따라 2026년부터 매년 0.5%p씩 올라 2033년 13%(근로자 6.5%)가 됩니다.
국민연금 기준소득월액은 {RATES_YEAR}년 7월부터 상한 {fmt(calc.PENSION_CAP_MONTHLY)}원·하한 {fmt(calc.PENSION_FLOOR_MONTHLY)}원이 적용됩니다.
출처: <a href="https://www.mohw.go.kr/board.es?mid=a10503010100&amp;bid=0027&amp;act=view&amp;list_no=1487279" target="_blank" rel="noopener">보건복지부 2026년 건강보험료율 결정</a>,
<a href="https://www.mohw.go.kr/board.es?act=view&amp;bid=0027&amp;list_no=1487817&amp;mid=a10503000000" target="_blank" rel="noopener">보건복지부 2026년 장기요양보험료율</a>,
<a href="https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0038M0.do" target="_blank" rel="noopener">국민연금공단 연금보험료 안내</a></p>

<h2>연봉 구간별 상세 계산 결과 ({len(salaries)}개)</h2>
<ul>{links}</ul>
{FOOTER_NAV}
<script>
{PERCENTILE_TABLE_JS}
{SALARY_CALC_JS}
</script>
</body></html>"""
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # sitemap.xml / robots.txt는 build.py가 전체 페이지 기준으로 생성
    print(f"생성 완료: {len(salaries)}개 페이지 + index.html -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
