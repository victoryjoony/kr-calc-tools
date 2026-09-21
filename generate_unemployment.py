"""
실업급여(구직급여) 계산기 페이지 생성 (고용보험법 기준, 인터랙티브 계산기)

1일 구직급여액 = 이직 전 평균임금 × 60% (상한 68,100원 / 하한 66,048원, 2026년 기준)
총 수급액 = 1일 구직급여액 × 소정급여일수(가입기간·연령별, 고용보험법 별표1)
"""
import os
from static_pages import SITE_NAME, GA_SNIPPET, FOOTER_NAV, SITE_STYLE, SITE_HEADER, FAVICON, seo_meta
from generate_severance import date_select_row, SERVICE_SPAN_JS

OUTPUT_DIR = "docs"

DAILY_CAP = 68100    # 2026년 상한액
DAILY_FLOOR = 66048  # 2026년 하한액 (최저임금 10,320원의 80% × 8시간)


def unemployment_html():
    title = "실업급여 계산기 - 구직급여 예상 수급액 2026"
    desc = "이직 전 3개월 급여, 가입기간, 연령을 입력하면 2026년 기준 구직급여 1일 지급액과 총 수급액을 계산해드립니다."

    return f"""<!doctype html>
<html lang="ko">
<head>
{GA_SNIPPET}
<meta charset="utf-8">
<title>{title}</title>
<meta name="description" content="{desc}">
{seo_meta("unemployment.html", title, desc, app_name="실업급여 계산기")}
<meta name="viewport" content="width=device-width, initial-scale=1">
{FAVICON}
<style>{SITE_STYLE}</style>
</head>
<body>
{SITE_HEADER}
  <h1>실업급여(구직급여) 계산기</h1>
  <p>이직 전 3개월 평균 급여, 고용보험 가입기간, 연령을 입력하면 2026년 기준 예상 구직급여를 계산합니다.</p>

  <div class="calc-box">
    <div class="field">
      <label for="monthly">이직 전 3개월 평균 월급여 (세전, 만원)</label>
      <input type="number" id="monthly" placeholder="예: 300" oninput="calc()">
    </div>
    <div class="field">
      <label>고용보험 가입일(입사일)</label>
      {date_select_row("start")}
    </div>
    <div class="field">
      <label>이직일(퇴사일)</label>
      {date_select_row("end")}
    </div>
    <div class="field checkbox">
      <input type="checkbox" id="senior" oninput="calc()">
      <label for="senior">만 50세 이상 또는 장애인</label>
    </div>

    <div class="result">
      <div class="result-row"><span>가입기간</span><span id="period">-</span></div>
      <div class="result-row"><span>소정급여일수</span><span id="days">-</span></div>
      <div class="result-row"><span>1일 구직급여액 (상한 {DAILY_CAP:,}원/하한 {DAILY_FLOOR:,}원 적용)</span><span id="daily">-</span></div>
      <div class="result-row total"><span>예상 총 수급액</span><span id="total">-</span></div>
    </div>
  </div>

  <h2>소정급여일수 (고용보험법 별표1)</h2>
  <table class="rule">
    <tr><th>가입기간</th><th>50세 미만</th><th>50세 이상·장애인</th></tr>
    <tr><td>1년 미만</td><td>120일</td><td>120일</td></tr>
    <tr><td>1~3년</td><td>150일</td><td>180일</td></tr>
    <tr><td>3~5년</td><td>180일</td><td>210일</td></tr>
    <tr><td>5~10년</td><td>210일</td><td>240일</td></tr>
    <tr><td>10년 이상</td><td>240일</td><td>270일</td></tr>
  </table>

  <h2>계산 기준</h2>
  <p>1일 구직급여액 = 이직 전 평균임금 × 60% (상한 {DAILY_CAP:,}원, 하한 {DAILY_FLOOR:,}원)<br>
  총 수급액 = 1일 구직급여액 × 소정급여일수</p>
  <p class="source">2026년 상한액·하한액 출처:
  <a href="https://v.daum.net/v/y9hcyWxpgW?f=p" target="_blank" rel="noopener nofollow">2026년 실업급여 상한액 인상 보도</a>
  (하한액은 2026년 최저임금 10,320원의 80%×8시간 기준)</p>

  <h2>수급 자격 요건 (계산기와 별개로 꼭 확인)</h2>
  <p>이 계산기는 금액만 추정합니다. 실제 수급을 위해서는 ① 이직일 이전 18개월간 피보험 단위기간
  180일 이상, ② 비자발적 이직(권고사직·계약만료·해고 등, 일부 정당한 자발적 이직 사유 포함) 요건을
  함께 충족해야 합니다. 단순 자발적 퇴사는 원칙적으로 수급 대상이 아닙니다.</p>

  <div class="disclaimer">
    ※ 세전 기준 추정치이며, 평균임금은 실제 근무일수 대신 3개월÷90일로 단순화했습니다. 정확한 금액과
    수급 자격은 고용노동부 고용보험 홈페이지 또는 관할 고용센터에서 확인하세요.
  </div>
  {FOOTER_NAV}
  <script>
  const DAILY_CAP = {DAILY_CAP};
  const DAILY_FLOOR = {DAILY_FLOOR};

  function benefitDays(years, senior) {{
    if (years < 1) return 120;
    if (years < 3) return senior ? 180 : 150;
    if (years < 5) return senior ? 210 : 180;
    if (years < 10) return senior ? 240 : 210;
    return senior ? 270 : 240;
  }}

{SERVICE_SPAN_JS}

  function calc() {{
    const monthly = parseFloat(document.getElementById('monthly').value) || 0;
    const start = readDateSelect('start');
    const end = readDateSelect('end');
    const senior = document.getElementById('senior').checked;
    if (!start || !end || monthly <= 0) return;

    const span = serviceSpan(start, end);
    if (span.totalDays <= 0) return;
    document.getElementById('period').textContent =
      span.years + '년 ' + span.remDays + '일 (총 ' + span.totalDays.toLocaleString() + '일)';

    const benefitDayCount = benefitDays(span.years, senior);
    document.getElementById('days').textContent = benefitDayCount + '일';

    const avgDailyWage = monthly * 3 / 90 * 10000;
    let dailyBenefit = Math.round(avgDailyWage * 0.6);
    if (dailyBenefit > DAILY_CAP) dailyBenefit = DAILY_CAP;
    if (dailyBenefit < DAILY_FLOOR) dailyBenefit = DAILY_FLOOR;

    const total = dailyBenefit * benefitDayCount;

    document.getElementById('daily').textContent = dailyBenefit.toLocaleString() + '원';
    document.getElementById('total').textContent = total.toLocaleString() + '원';
  }}

  window.addEventListener('DOMContentLoaded', function() {{
    const params = new URLSearchParams(window.location.search);
    const monthly = params.get('monthly');
    if (monthly) {{
      document.getElementById('monthly').value = monthly;
      calc();
    }}
  }});
  </script>
</body>
</html>"""


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "unemployment.html"), "w", encoding="utf-8") as f:
        f.write(unemployment_html())
    print("실업급여 계산기 페이지 생성 완료 -> docs/unemployment.html")


if __name__ == "__main__":
    main()
