"""
연봉 실수령액 계산 로직 (2026년 기준 근사치)

주의: 4대보험 요율/상한액은 매년(국민연금 상·하한은 7월, 요율은 1월) 변경됩니다.
갱신 시 아래 공식 출처에서 최신 수치를 확인하고 RATES_YEAR도 함께 바꿀 것.
- 국민연금 요율/상·하한액: 국민연금공단 고시 (연금개혁으로 2026년부터 매년 0.5%p 인상, 2033년 13%까지)
- 건강보험료율/장기요양보험료율: 보건복지부 보도자료 (매년 8~9월 다음 해 요율 결정)
- 소득세: 국세청 근로소득 간이세액표 (여기서는 연간 산출식 기반 근사치 사용,
  1인 가구 기준으로 기본공제·연금보험료공제·특별소득공제(건강보험료)만 반영한
  단순화 모델. 부양가족, 카드사용액 등 그 외 소득/세액공제는 미반영이라
  실제 원천징수와는 여전히 오차가 있을 수 있음)
"""

RATES_YEAR = 2026  # 페이지 제목/안내문의 "OOOO년 기준" 표기에 사용

# 최저임금 (고용노동부 고시, 매년 8월 초 다음 해 금액 확정) - 실수령액표 페이지의 최저임금 월급 안내에 사용
MINIMUM_WAGE_HOURLY = 10_320         # 2026년 시급
MINIMUM_WAGE_MONTHLY_HOURS = 209     # 주 40시간 + 주휴 포함 월 환산 시간

# ---- 4대보험 요율 (2026년, 매년 갱신 필요) ----
PENSION_RATE = 0.0475         # 국민연금 근로자 부담 4.75% (총 9.5%, 2026.1~)
PENSION_CAP_MONTHLY = 6_590_000   # 기준소득월액 상한 (2026.7~2027.6)
PENSION_FLOOR_MONTHLY = 410_000   # 기준소득월액 하한 (2026.7~2027.6)

HEALTH_RATE = 0.03595         # 건강보험 근로자 부담 3.595% (총 7.19%)
LONGTERM_CARE_RATE_OF_HEALTH = 0.1314  # 장기요양보험 = 건강보험료의 13.14%

EMPLOYMENT_RATE = 0.009       # 고용보험 근로자 부담 0.9%

# 직전 연도 요율 (홈페이지 "올해 달라진 요율" 비교표용). 요율 갱신 시 위의 현재 값을 여기로 옮길 것
PREVIOUS_YEAR_RATES = {
    "year": 2025,
    "pension": 0.045,
    "health": 0.03545,
    "longterm_care_of_health": 0.1295,
    "employment": 0.009,
}

# ---- 근로소득공제 구간 (소득세법 제47조, 한도 2,000만원) ----
EARNED_INCOME_DEDUCTION_CAP = 20_000_000

def earned_income_deduction(gross_annual):
    g = gross_annual
    if g <= 5_000_000:
        return g * 0.7
    if g <= 15_000_000:
        return 3_500_000 + (g - 5_000_000) * 0.4
    if g <= 45_000_000:
        return 7_500_000 + (g - 15_000_000) * 0.15
    if g <= 100_000_000:
        return 12_000_000 + (g - 45_000_000) * 0.05
    return min(14_750_000 + (g - 100_000_000) * 0.02, EARNED_INCOME_DEDUCTION_CAP)

# ---- 종합소득세 누진세율표 (과세표준, 세율, 누진공제) ----
TAX_BRACKETS = [
    (12_000_000, 0.06, 0),
    (46_000_000, 0.15, 1_080_000),
    (88_000_000, 0.24, 5_220_000),
    (150_000_000, 0.35, 14_900_000),
    (300_000_000, 0.38, 19_400_000),
    (500_000_000, 0.40, 25_400_000),
    (1_000_000_000, 0.42, 35_400_000),
    (float("inf"), 0.45, 65_400_000),
]

def calc_tax_by_bracket(base):
    if base <= 0:
        return 0
    for limit, rate, deduction in TAX_BRACKETS:
        if base <= limit:
            return base * rate - deduction
    return 0

def earned_income_tax_credit(calculated_tax, gross_annual):
    # 근로소득세액공제 (소득세법 제59조)
    if calculated_tax <= 1_300_000:
        credit = calculated_tax * 0.55
    else:
        credit = 715_000 + (calculated_tax - 1_300_000) * 0.3

    if gross_annual <= 33_000_000:
        cap = 740_000
    elif gross_annual <= 70_000_000:
        cap = max(660_000, 740_000 - (gross_annual - 33_000_000) * 0.008)
    elif gross_annual <= 120_000_000:
        cap = max(500_000, 660_000 - (gross_annual - 70_000_000) * 0.5)
    else:
        cap = max(200_000, 500_000 - (gross_annual - 120_000_000) * 0.5)

    return min(credit, cap)


def calculate(gross_annual: int) -> dict:
    """연봉(원)을 받아 4대보험/소득세 공제 후 월 실수령액을 계산."""
    gross_monthly = gross_annual / 12

    # 국민연금: 기준소득월액에 상/하한 적용
    pension_base = min(max(gross_monthly, PENSION_FLOOR_MONTHLY), PENSION_CAP_MONTHLY)
    pension = round(pension_base * PENSION_RATE)

    health = round(gross_monthly * HEALTH_RATE)
    longterm_care = round(health * LONGTERM_CARE_RATE_OF_HEALTH)
    employment = round(gross_monthly * EMPLOYMENT_RATE)

    # 4대보험 연간 합계 (연금보험료공제 / 특별소득공제에 사용)
    pension_annual = pension * 12
    health_and_longterm_annual = (health + longterm_care) * 12

    # 소득세 (연간 기준 근사 계산 후 12개월 분할)
    deduction = earned_income_deduction(gross_annual)
    earned_income_amount = max(gross_annual - deduction, 0)

    # 종합소득공제 = 기본공제(본인) + 연금보험료공제(국민연금 전액) + 특별소득공제(건강보험료 전액)
    basic_deduction = 1_500_000
    comprehensive_deduction = basic_deduction + pension_annual + health_and_longterm_annual
    taxable_base = max(earned_income_amount - comprehensive_deduction, 0)

    calculated_tax = calc_tax_by_bracket(taxable_base)
    credit = earned_income_tax_credit(calculated_tax, gross_annual)
    final_tax_annual = max(calculated_tax - credit, 0)

    income_tax = round(final_tax_annual / 12)
    local_tax = round(income_tax * 0.1)  # 지방소득세 = 소득세의 10%

    total_deduction = pension + health + longterm_care + employment + income_tax + local_tax
    net_monthly = round(gross_monthly - total_deduction)

    return {
        "gross_annual": gross_annual,
        "gross_monthly": round(gross_monthly),
        "pension": pension,
        "health": health,
        "longterm_care": longterm_care,
        "employment": employment,
        "income_tax": income_tax,
        "local_tax": local_tax,
        "total_deduction": total_deduction,
        "net_monthly": net_monthly,
        "net_annual": net_monthly * 12,
        # 계산 과정 설명용 중간값
        "earned_income_deduction": round(deduction),
        "earned_income_amount": round(earned_income_amount),
        "comprehensive_deduction": round(comprehensive_deduction),
        "taxable_base": round(taxable_base),
        "calculated_tax_annual": round(calculated_tax),
        "tax_credit_annual": round(credit),
        "final_tax_annual": round(final_tax_annual),
    }


if __name__ == "__main__":
    for salary in [30_000_000, 36_000_000, 50_000_000, 80_000_000]:
        r = calculate(salary)
        print(f"연봉 {salary:,}원 -> 월 실수령액 약 {r['net_monthly']:,}원 (공제 {r['total_deduction']:,}원)")
