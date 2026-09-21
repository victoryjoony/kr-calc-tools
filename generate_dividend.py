"""
배당금 계산기 페이지 생성 (종목 선택 기반, 인터랙티브)

투자자문이 아닌 정보 제공 목적: 배당금(DPS)은 공시된 확정 사실만 사용하고,
배당수익률은 사용자가 직접 입력한 매수단가로 계산한다(임의의 현재 주가를 단정하지 않음).
"""
import os
import json
from static_pages import SITE_NAME, GA_SNIPPET, FOOTER_NAV, SITE_STYLE, SITE_HEADER, FAVICON, seo_meta
from dividend_data import STOCKS, PRICE_DATE

OUTPUT_DIR = "docs"


def dividend_html():
    title = "배당금 계산기 - 삼성전자·4대금융지주·SK텔레콤·KT&G"
    desc = "보유 주식 수를 입력하면 2025년 확정 배당금 기준 세후 배당 실수령액을 계산해드립니다."

    options = "\n".join(
        f'<option value="{s["id"]}">{s["name"]} (연 {s["dps"]:,}원/주, 배당률 {s["yield_pct"]}%)</option>' for s in STOCKS
    )
    stock_data_json = json.dumps(
        {s["id"]: {"name": s["name"], "dps": s["dps"], "price": s["price"]} for s in STOCKS},
        ensure_ascii=False,
    )

    table_rows = "\n".join(
        f'<tr><td>{s["name"]}</td><td class="num">{s["dps"]:,}원</td>'
        f'<td class="num">{s["price"]:,}원</td><td class="num">{s["yield_pct"]}%</td>'
        f'<td class="source"><a href="{s["source_url"]}" target="_blank" rel="noopener nofollow">출처</a></td></tr>'
        for s in STOCKS
    )
    notes = "\n".join(f'<li><b>{s["name"]}</b>: {s["note"]}</li>' for s in STOCKS)

    return f"""<!doctype html>
<html lang="ko">
<head>
{GA_SNIPPET}
<meta charset="utf-8">
<title>{title}</title>
<meta name="description" content="{desc}">
{seo_meta("dividend.html", title, desc, app_name="배당금 계산기")}
<meta name="viewport" content="width=device-width, initial-scale=1">
{FAVICON}
<style>{SITE_STYLE}</style>
</head>
<body>
{SITE_HEADER}
  <h1>배당금 계산기</h1>
  <p>종목과 보유 주식 수를 입력하면 2025년 확정 배당금(DPS) 기준 세전/세후 배당금을 계산합니다.</p>

  <div class="calc-box">
    <div class="field">
      <label for="stock">종목 선택</label>
      <select id="stock" onchange="calc()">
        {options}
      </select>
    </div>
    <div class="field">
      <label for="shares">보유 주식 수</label>
      <input type="number" id="shares" placeholder="예: 100" oninput="calc()">
    </div>
    <div class="field">
      <label for="price">매수단가 (원, 비워두면 {PRICE_DATE} 종가로 자동 계산)</label>
      <input type="number" id="price" placeholder="예: 85000" oninput="calc()">
    </div>

    <div class="result">
      <div class="result-row"><span>연간 세전 배당금</span><span id="gross">-</span></div>
      <div class="result-row"><span>배당소득세 (15.4%)</span><span id="tax">-</span></div>
      <div class="result-row total"><span>연간 세후 실수령 배당금</span><span id="net">-</span></div>
      <div class="result-row"><span>배당수익률</span><span id="yield">-</span></div>
    </div>
    <div class="stock-note" id="note"></div>
  </div>

  <h2>2025년 확정 연간 배당금(DPS) 및 배당수익률 비교</h2>
  <table class="rule">
    <tr><th>종목</th><th>연간 배당금</th><th>주가({PRICE_DATE})</th><th>배당수익률</th><th>출처</th></tr>
    {table_rows}
  </table>
  <p class="source" style="margin-top:8px">배당수익률 = 연간 배당금 ÷ {PRICE_DATE} 종가. 배당 발표 시점(1~2월) 뉴스에서는 우리금융지주·하나금융지주가
  6~7%대 고배당으로 보도됐지만, 이후 4대 금융지주 주가가 크게 오르면서(2년 새 시총 2배 언급도 있음) {PRICE_DATE}
  기준 수익률은 표와 같이 낮아졌습니다. 배당수익률은 주가에 따라 매일 바뀌는 값이니, 위 표는 참고용 스냅샷이고
  정확한 값은 매수 시점 주가로 직접 다시 계산하세요.</p>

  <h2>종목별 참고사항</h2>
  <ul>{notes}</ul>

  <h2>배당소득세는 왜 15.4%인가</h2>
  <p>국내 상장주식 배당소득에는 소득세 14% + 지방소득세 1.4%가 원천징수됩니다. 단, 금융소득(이자+배당)이
  연 2,000만원을 넘으면 다른 소득과 합산해 종합과세되어 세율이 달라질 수 있습니다.</p>

  <div class="disclaimer">
    ※ 본 계산기는 투자자문이나 특정 종목 매수 추천이 아닌 정보 제공용 도구입니다. 배당금은 매년 이사회
    결의로 증액·감액·중단될 수 있으며 과거 배당이 미래 배당을 보장하지 않습니다. 배당수익률이 비정상적으로
    높게 보이는 경우 주가 급락에 따른 "고배당의 함정"일 수 있으니 배당성향·실적 추이를 함께 확인하세요.
    최신 공시는 <a href="https://dart.fss.or.kr" target="_blank" rel="noopener nofollow">DART 전자공시시스템</a>에서
    확인할 수 있습니다.
  </div>
  {FOOTER_NAV}
  <script>
  const STOCKS = {stock_data_json};

  function calc() {{
    const stockId = document.getElementById('stock').value;
    const shares = parseFloat(document.getElementById('shares').value) || 0;
    const priceInput = document.getElementById('price');
    const stock = STOCKS[stockId];
    if (!stock) return;

    if (!priceInput.value) priceInput.placeholder = stock.price.toLocaleString();
    const price = parseFloat(priceInput.value) || stock.price;

    if (shares > 0) {{
      const gross = stock.dps * shares;
      const tax = Math.round(gross * 0.154);
      const net = gross - tax;
      document.getElementById('gross').textContent = gross.toLocaleString() + '원';
      document.getElementById('tax').textContent = tax.toLocaleString() + '원';
      document.getElementById('net').textContent = net.toLocaleString() + '원';
    }}

    const yieldPct = (stock.dps / price * 100).toFixed(2);
    document.getElementById('yield').textContent = yieldPct + '%' + (priceInput.value ? '' : ' (기준가 ' + stock.price.toLocaleString() + '원)');
  }}
  window.onload = calc;
  </script>
</body>
</html>"""


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "dividend.html"), "w", encoding="utf-8") as f:
        f.write(dividend_html())
    print("배당금 계산기 페이지 생성 완료 -> docs/dividend.html")


if __name__ == "__main__":
    main()
