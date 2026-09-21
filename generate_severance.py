"""
퇴직금 계산기 페이지 생성 (근로기준법 평균임금 기준 퇴직금 + 퇴직소득세·세후 실수령액, 인터랙티브 계산기)

법정 퇴직금 = 1일 평균임금 × 30일 × (재직일수 ÷ 365)
평균임금(1일) = 퇴직 전 3개월간 임금총액 ÷ 그 기간의 총 일수(약 90일)
(근로자퇴직급여 보장법 제8조, 근로기준법 제2조)

재직일수는 입사일부터 마지막 근무일까지 양 끝을 모두 포함해 센다
(고용노동부 계산기의 '퇴직일 = 마지막 근무일 다음날'로 뺀 값과 같음).

퇴직소득세는 calc.retirement_income_tax와 같은 공식을 JS로 옮긴 것
(소득세법 제48조·제55조, 국세청 "퇴직소득세 계산방법"). 세율표는 calc.TAX_BRACKETS에서 주입.
"""
import os
import json
import calc
from calc import RATES_YEAR, retirement_income_tax
from static_pages import SITE_NAME, GA_SNIPPET, FOOTER_NAV, SITE_STYLE, SITE_HEADER, FAVICON, seo_meta

OUTPUT_DIR = "docs"

YEAR_START = 1970
YEAR_END = 2030

# 페이지 본문의 계산 예시 (값은 retirement_income_tax로 생성 → 공식과 어긋날 일 없음)
EXAMPLE_PAY = 50_000_000
EXAMPLE_YEARS = 10

TAX_BRACKETS_JS = json.dumps(
    [[None if limit == float("inf") else limit, rate, ded] for limit, rate, ded in calc.TAX_BRACKETS]
)

# 연/월/일 드롭다운 날짜 읽기 + 재직(가입)기간 계산. 실업급여 계산기도 같이 씀
SERVICE_SPAN_JS = """
function readDateSelect(prefix) {
  const y = document.getElementById(prefix + 'Year').value;
  const m = document.getElementById(prefix + 'Month').value;
  const d = document.getElementById(prefix + 'Day').value;
  if (!y || !m || !d) return null;
  return new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
}

// 시작일~마지막 근무일(포함) → 만 연수, 남은 일수, 총 일수 (딱 1년 근무 = 1년 0일)
function serviceSpan(start, lastDay) {
  const endEx = new Date(lastDay.getFullYear(), lastDay.getMonth(), lastDay.getDate() + 1);
  const totalDays = Math.round((endEx - start) / 86400000);
  const anniversary = (n) => new Date(start.getFullYear() + n, start.getMonth(), start.getDate());
  let years = endEx.getFullYear() - start.getFullYear();
  if (anniversary(years) > endEx) years -= 1;
  const remDays = Math.round((endEx - anniversary(years)) / 86400000);
  return { years, remDays, totalDays };
}
"""

SEVERANCE_JS = SERVICE_SPAN_JS + """
const TAX_BRACKETS = __TAX_BRACKETS__.map(([l, r, d]) => [l === null ? Infinity : l, r, d]);

function taxByBracket(base) {
  if (base <= 0) return 0;
  for (const [limit, rate, deduction] of TAX_BRACKETS) {
    if (base <= limit) return base * rate - deduction;
  }
  return 0;
}

function serviceYearsDeduction(n) {
  if (n <= 5) return 1000000 * n;
  if (n <= 10) return 5000000 + 2000000 * (n - 5);
  if (n <= 20) return 15000000 + 2500000 * (n - 10);
  return 40000000 + 3000000 * (n - 20);
}

function convertedPayDeduction(c) {
  if (c <= 8000000) return c;
  if (c <= 70000000) return 8000000 + (c - 8000000) * 0.6;
  if (c <= 100000000) return 45200000 + (c - 70000000) * 0.55;
  if (c <= 300000000) return 61700000 + (c - 100000000) * 0.45;
  return 151700000 + (c - 300000000) * 0.35;
}

function retirementIncomeTax(pay, taxYears) {
  const yearsDed = Math.min(serviceYearsDeduction(taxYears), pay);
  const converted = (pay - yearsDed) * 12 / taxYears;
  const convertedDed = convertedPayDeduction(converted);
  const base = Math.max(converted - convertedDed, 0);
  const convertedTax = taxByBracket(base);
  const incomeTax = Math.floor(Math.round(convertedTax * taxYears / 12) / 10) * 10;
  const localTax = Math.floor(Math.floor(incomeTax / 10) / 10) * 10;
  return { yearsDed, converted, convertedDed, base, convertedTax, incomeTax, localTax,
           net: Math.round(pay) - incomeTax - localTax };
}

const won = (n) => Math.round(n).toLocaleString() + '원';

function calc() {
  const start = readDateSelect('start');
  const last = readDateSelect('end');
  if (!start || !last) return;
  const span = serviceSpan(start, last);
  if (span.totalDays <= 0) return;

  document.getElementById('period').textContent =
    span.years + '년 ' + span.remDays + '일 (총 ' + span.totalDays.toLocaleString() + '일)';
  document.getElementById('warning').style.display = span.years < 1 ? 'block' : 'none';

  const monthly = parseFloat(document.getElementById('monthly').value) || 0;
  const knownMan = parseFloat(document.getElementById('knownPay').value) || 0;
  const avgWage = Math.round((monthly * 3 / 90) * 10000);
  document.getElementById('avgwage').textContent = monthly > 0 ? won(avgWage) : '-';

  // 회사에서 받을 퇴직금을 직접 입력했으면 그 금액으로 세금 계산
  const pay = knownMan > 0 ? knownMan * 10000 : Math.round(avgWage * 30 * (span.totalDays / 365));
  if (pay <= 0) return;
  document.getElementById('gross').textContent = won(pay) + (knownMan > 0 ? ' (입력값)' : '');

  const taxYears = Math.max(1, span.years + (span.remDays > 0 ? 1 : 0));
  const t = retirementIncomeTax(pay, taxYears);
  document.getElementById('taxYears').textContent = taxYears + '년';
  document.getElementById('incomeTax').textContent = won(t.incomeTax);
  document.getElementById('localTax').textContent = won(t.localTax);
  document.getElementById('net').textContent = won(t.net);

  const steps = [
    '세법상 근속연수 = ' + taxYears + '년 (1년 미만 기간은 1년으로 올림)',
    '근속연수공제 = ' + won(t.yearsDed),
    '환산급여 = (퇴직금 − 근속연수공제) × 12 ÷ ' + taxYears + '년 = ' + won(t.converted),
    '환산급여공제 = ' + won(t.convertedDed),
    '과세표준 = 환산급여 − 환산급여공제 = ' + won(t.base),
    '환산산출세액 = 과세표준 × 기본세율 = ' + won(t.convertedTax),
    '퇴직소득세 = 환산산출세액 ÷ 12 × ' + taxYears + '년 = ' + won(t.incomeTax),
  ];
  const ol = document.getElementById('taxSteps');
  ol.innerHTML = '';
  for (const s of steps) {
    const li = document.createElement('li');
    li.textContent = s;
    ol.appendChild(li);
  }
  document.getElementById('taxStepsBox').style.display = 'block';
}

window.addEventListener('DOMContentLoaded', function() {
  const params = new URLSearchParams(window.location.search);
  const monthly = params.get('monthly');
  if (monthly) {
    document.getElementById('monthly').value = monthly;
    calc();
  }
});
""".replace("__TAX_BRACKETS__", TAX_BRACKETS_JS)


def fmt(n):
    return f"{n:,}"


def year_options():
    return "\n".join(f'<option value="{y}">{y}년</option>' for y in range(YEAR_END, YEAR_START - 1, -1))


def month_options():
    return "\n".join(f'<option value="{m}">{m}월</option>' for m in range(1, 13))


def day_options():
    return "\n".join(f'<option value="{d}">{d}일</option>' for d in range(1, 32))


def date_select_row(prefix):
    return f"""<div class="date-select-row">
      <select id="{prefix}Year" onchange="calc()"><option value="">연도</option>{year_options()}</select>
      <select id="{prefix}Month" onchange="calc()"><option value="">월</option>{month_options()}</select>
      <select id="{prefix}Day" onchange="calc()"><option value="">일</option>{day_options()}</select>
    </div>"""


def severance_html():
    title = f"퇴직금 계산기 {RATES_YEAR} - 퇴직소득세 떼고 실수령액까지 바로 계산"
    desc = ("입사일, 퇴사일, 최근 3개월 급여만 입력하면 법정 퇴직금과 퇴직소득세(지방소득세 포함), "
            "세후 실수령액을 바로 계산합니다. 국세청 퇴직소득세 계산 방법 기준.")
    ex = retirement_income_tax(EXAMPLE_PAY, EXAMPLE_YEARS)
    ex_rate = round((ex["income_tax"] + ex["local_tax"]) / EXAMPLE_PAY * 100, 1)

    return f"""<!doctype html>
<html lang="ko">
<head>
{GA_SNIPPET}
<meta charset="utf-8">
<title>{title}</title>
<meta name="description" content="{desc}">
{seo_meta("severance.html", title, desc, app_name="퇴직금 계산기")}
<meta name="viewport" content="width=device-width, initial-scale=1">
{FAVICON}
<style>{SITE_STYLE}</style>
</head>
<body>
{SITE_HEADER}
  <h1>퇴직금 계산기 (퇴직소득세·실수령액 포함)</h1>
  <p>입사일과 마지막 근무일, 퇴직 전 3개월 평균 월급여를 입력하면 근로기준법 기준 퇴직금과
  퇴직소득세를 뗀 실수령액까지 계산합니다.</p>

  <div class="calc-box">
    <div class="field">
      <label>입사일</label>
      {date_select_row("start")}
    </div>
    <div class="field">
      <label>퇴사일 (마지막 근무일, 예정일도 가능)</label>
      {date_select_row("end")}
    </div>
    <div class="field">
      <label for="monthly">퇴직 전 3개월 평균 월급여 (세전, 만원)</label>
      <input type="number" id="monthly" placeholder="예: 350" oninput="calc()">
    </div>
    <div class="field">
      <label for="knownPay">퇴직금을 이미 알고 있다면 (세전, 만원 · 선택)</label>
      <input type="number" id="knownPay" placeholder="회사에서 안내받은 금액으로 세금만 계산" oninput="calc()">
    </div>

    <div class="warning" id="warning">
      ⚠ 재직기간이 1년 미만입니다. 근로자퇴직급여 보장법상 1년 미만 근속자는 법정 퇴직금 지급 의무가
      없습니다 (회사 자체 규정으로 지급하는 경우는 있을 수 있음).
    </div>

    <div class="result">
      <div class="result-row"><span>재직기간</span><span id="period">-</span></div>
      <div class="result-row"><span>1일 평균임금 (월급여×3÷90)</span><span id="avgwage">-</span></div>
      <div class="result-row"><span>퇴직금 (세전)</span><span id="gross">-</span></div>
      <div class="result-row"><span>세법상 근속연수</span><span id="taxYears">-</span></div>
      <div class="result-row"><span>퇴직소득세</span><span id="incomeTax">-</span></div>
      <div class="result-row"><span>지방소득세</span><span id="localTax">-</span></div>
      <div class="result-row total"><span>세후 실수령액</span><span id="net">-</span></div>
    </div>

    <div class="explain" id="taxStepsBox" style="display:none">
      <h2>내 퇴직소득세 계산 과정</h2>
      <ol class="steps" id="taxSteps"></ol>
    </div>
  </div>

  <h2>계산 기준</h2>
  <p>퇴직금 = 1일 평균임금 × 30일 × (재직일수 ÷ 365)<br>
  1일 평균임금 = 퇴직 전 3개월 임금총액 ÷ 약 90일 (달력상 실제 일수 대신 단순화한 값)<br>
  재직일수는 입사일부터 마지막 근무일까지 포함해 셉니다.</p>
  <p class="source">법적 근거: 근로자퇴직급여 보장법 제8조, 근로기준법 제2조 — 정확한 산정은
  <a href="https://www.moel.go.kr/retirementpayCal.do" target="_blank" rel="noopener nofollow">고용노동부 퇴직금 계산기</a>에서
  실제 근무일수 기준으로 다시 확인하는 것을 권장합니다.</p>

  <h2>퇴직소득세 계산 방법</h2>
  <p>퇴직소득세는 퇴직금을 근속연수로 나눠 1년치 소득처럼 바꾼 뒤(환산급여) 세율을 매기고, 다시 근속연수만큼
  곱하는 방식이라 오래 일할수록 세금 부담이 크게 줄어듭니다. 예를 들어 퇴직금 {fmt(EXAMPLE_PAY)}원, 근속 {EXAMPLE_YEARS}년이면:</p>
  <ol class="steps">
    <li>근속연수공제 = <span class="num">{fmt(ex["service_years_deduction"])}원</span></li>
    <li>환산급여 = (퇴직금 − 근속연수공제) × 12 ÷ 근속연수 = <span class="num">{fmt(ex["converted_pay"])}원</span></li>
    <li>환산급여공제 = <span class="num">{fmt(ex["converted_pay_deduction"])}원</span></li>
    <li>과세표준 = 환산급여 − 환산급여공제 = <span class="num">{fmt(ex["tax_base"])}원</span></li>
    <li>환산산출세액 = 과세표준 × 기본세율(6~45%) = <span class="num">{fmt(ex["converted_tax"])}원</span></li>
    <li>퇴직소득세 = 환산산출세액 ÷ 12 × 근속연수 = <span class="num">{fmt(ex["income_tax"])}원</span>
      (+ 지방소득세 {fmt(ex["local_tax"])}원)</li>
  </ol>
  <p>→ 세후 퇴직금은 <b>{fmt(ex["net_pay"])}원</b>으로, 세금은 퇴직금의 약 {ex_rate}%입니다.</p>
  <p class="source">근속연수공제·환산급여공제 기준: 소득세법 제48조,
  <a href="https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=6444&amp;cntntsId=7880" target="_blank" rel="noopener nofollow">국세청 퇴직소득세 계산방법</a></p>

  <h2>퇴직금을 IRP 계좌로 받으면 세금은?</h2>
  <p>55세 이전에 퇴직하면 퇴직금은 원칙적으로 개인형 퇴직연금(IRP) 계좌로 입금됩니다(55세 이후 퇴직, 소액 등은 예외).
  이때는 퇴직소득세를 바로 떼지 않고 IRP에서 돈을 찾을 때 내며(과세이연), 55세 이후 연금으로 나눠 받으면
  퇴직소득세가 30~40% 줄어듭니다. 이 계산기의 세후 금액은 일시금으로 받을 때 기준입니다.</p>
  <p class="source">참고:
  <a href="https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&amp;csmSeq=2056&amp;ccfNo=3&amp;cciNo=1&amp;cnpClsNo=1" target="_blank" rel="noopener nofollow">찾기쉬운 생활법령정보 — 퇴직연금</a></p>

  <h2>퇴직금이란?</h2>
  <p>계속근로기간 1년 이상인 근로자가 퇴직할 때 사용자가 지급해야 하는 법정 급여입니다. 4주 평균
  1주 소정근로시간이 15시간 이상이면 정규직·계약직·아르바이트 구분 없이 적용됩니다. 상여금, 연차수당
  중 일부가 평균임금 산정에 포함되는 경우도 있어 실제 금액은 이 계산기보다 높게 나올 수 있습니다.</p>

  <div class="disclaimer">
    ※ 평균임금은 실제 근무일수·상여금·연차수당 반영분에 따라 이 계산기의 단순화된 결과와 차이가 날 수 있으며,
    퇴직소득세는 비과세 소득·중간정산 이력 등이 없는 일반적인 경우를 가정한 추정치입니다. 정확한 금액은 위
    고용노동부 계산기, 국세청 홈택스 퇴직소득 모의계산 또는 회사 인사팀을 통해 확인하세요.
  </div>
  {FOOTER_NAV}
  <script>
{SEVERANCE_JS}
  </script>
</body>
</html>"""


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "severance.html"), "w", encoding="utf-8") as f:
        f.write(severance_html())
    print("퇴직금 계산기 페이지 생성 완료 -> docs/severance.html")


if __name__ == "__main__":
    main()
