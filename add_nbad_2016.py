import csv
import hashlib
import io
from pathlib import Path

CSV_PATH = Path("output/NBAD_raw_financial_data.csv")
BACKUP_PATH = Path(
    "output/backups/NBAD_raw_financial_data_before_2016.csv"
)

# Verify the original dataset has not changed since backup.
original_bytes = CSV_PATH.read_bytes()
backup_bytes = BACKUP_PATH.read_bytes()

assert hashlib.sha256(original_bytes).digest() == hashlib.sha256(
    backup_bytes
).digest(), "Current CSV differs from the verified backup."

with CSV_PATH.open("r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames
    rows = list(reader)

assert columns is not None
assert len(columns) == 58
assert len(rows) == 6
assert [r["Year"] for r in rows] == [
    "2010", "2011", "2012", "2013", "2014", "2015"
]

if any(r["Year"] == "2016" for r in rows):
    raise SystemExit("NBAD 2016 already exists. No changes made.")

previous = next(r for r in rows if r["Year"] == "2015")

def previous_value(column):
    return float(previous[column])

def rounded(value):
    return round(value, 2)

# All financial amounts are AED millions.
assets = 420713.500
liabilities = 374207.997
equity = 46505.503

tier_1_capital_notes = 6754.750
shareholders_equity = equity - tier_1_capital_notes

net_profit = 5296.042
tier_1_coupon = 283.415
profit_attributable = net_profit - tier_1_coupon

operating_income = 10808.184
operating_expenses = 4012.759

prev_assets = previous_value(
    "Total_Assets_LCU_Millions"
)
prev_equity = previous_value(
    "Total_Equity_LCU_Millions"
)
prev_shareholders_equity = previous_value(
    "Shareholders_Equity_LCU_Millions"
)

avg_assets = (assets + prev_assets) / 2
avg_equity = (equity + prev_equity) / 2
avg_shareholders_equity = (
    shareholders_equity + prev_shareholders_equity
) / 2

# Audited financial statement reconciliation checks.
assert round(assets - liabilities - equity, 6) == 0

assert round(
    45758.957 + 3319.705, 3
) == 49078.662

assert round(
    228092.256 + 24593.160 + 18630.206, 3
) == 271315.622

assert round(
    208097.925 - 1156.681 - 6409.433, 3
) == 200531.811

assert round(
    operating_income - operating_expenses
    - 1190.677, 3
) == 5604.748

assert round(
    5604.748 - 308.706, 3
) == net_profit

assert round(
    6748.321 - 1156.681, 3
) == 5591.640

assert round(
    49078.662 / 271315.622 * 100, 2
) == 18.09

record = {column: "" for column in columns}

record.update({
    "Bank_Name": "National Bank of Abu Dhabi",
    "Country": "United Arab Emirates",
    "Year": "2016",

    "Total_Assets_LCU_Millions": assets,
    "Total_Liabilities_LCU_Millions": liabilities,
    "Total_Equity_LCU_Millions": equity,
    "Shareholders_Equity_LCU_Millions": shareholders_equity,

    "Net_Profit_LCU_Millions": net_profit,
    "Profit_Before_Taxation_LCU_Millions": 5604.748,
    "Total_Operating_Income_LCU_Millions": operating_income,
    "Operating_Expenses_LCU_Millions": operating_expenses,
    "Net_Interest_Income_LCU_Millions": 6820.303,
    "Net_Impairment_Charge_LCU_Millions": 1190.677,

    "Loans_Advances_Islamic_Financing_LCU_Millions": 200531.811,
    "Gross_Loans_LCU_Millions": 208097.925,
    "Customer_Accounts_Other_Deposits_LCU_Millions": 253382.492,

    # Non-performing loans net of suspended interest.
    "Non_Performing_Loans_LCU_Millions": 5591.640,

    # IFRS 9 Stage 3 classification not applicable in 2016.
    # Separate regulatory AT1 amount not independently verified.

    "Total_Regulatory_Capital_LCU_Millions": 49078.662,
    "Eligible_Tier_1_Capital_LCU_Millions": 45758.957,
    "Tier_2_Capital_LCU_Millions": 3319.705,

    "Credit_Risk_RWA_LCU_Millions": 228092.256,
    "Market_Risk_RWA_LCU_Millions": 24593.160,
    "Operational_Risk_RWA_LCU_Millions": 18630.206,
    "RWA_LCU_Millions": 271315.622,

    "Published_CAR_Pct": 18.09,
    "Reporting_Currency": "AED",
    "Reporting_Unit": "Millions",

    "Source_Document": "nbad-2016-annual-report-eng.pdf",
    "Source_PDF_Page": "53-54",
    "Source_Printed_Pages": "8-9",
    "Gross_Loans_Source_PDF_Page": 109,
    "NPL_Source_PDF_Page": "17,83,85",
    "CAR_Source_PDF_Page": 100,

    "Entity_Basis_Note": (
        "NBAD consolidated financial statements; AED thousands "
        "converted to AED millions. Balance sheet PDF page 53 "
        "(OCR verified by reconciliation); profit or loss PDF page 54. "
        "Gross loans AED 208097.925 million from PDF page 109. "
        "Gross non-performing loans AED 6748.321 million from "
        "PDF pages 83 and 85. Interest suspended AED 1156.681 "
        "million deducted to obtain net NPL AED 5591.640 million. "
        "Published NPL ratio 2.70% from PDF page 17; ratio "
        "definition and rounding may differ from a simple "
        "division using reported gross loans. "
        "Tier 1 capital notes AED 6754.750 million excluded "
        "from ordinary shareholders equity. Tier 1 coupon "
        "AED 283.415 million deducted from net profit for "
        "calculated ROE; verified in changes in equity and "
        "cash flows on PDF pages 56-57. "
        "Published return on shareholders funds 13.1% "
        "from PDF page 41. Published NIM 1.92% from PDF "
        "pages 16 and 41. The 2016 report shows comparative "
        "2015 NIM of 2.01%, whereas the existing 2015 dataset "
        "uses 1.97% from its original report; 2015 retained "
        "unchanged. IFRS 9 Stage 3 fields not applicable "
        "to 2016. Separate regulatory Additional Tier 1 "
        "capital figure not independently verified."
    ),

    "NPL_Ratio_Pct": 2.70,
    "CAR_Pct": 18.09,

    "CIR_Pct": rounded(
        operating_expenses / operating_income * 100
    ),

    "Previous_Year_Total_Assets_LCU_Millions": prev_assets,
    "Previous_Year_Total_Equity_LCU_Millions": prev_equity,
    "Previous_Year_Shareholders_Equity_LCU_Millions": (
        prev_shareholders_equity
    ),

    "Average_Total_Assets_LCU_Millions": round(
        avg_assets, 4
    ),
    "Average_Total_Equity_LCU_Millions": round(
        avg_equity, 4
    ),
    "Average_Shareholders_Equity_LCU_Millions": round(
        avg_shareholders_equity, 4
    ),

    "Profit_Attributable_To_Shareholders_LCU_Millions": (
        profit_attributable
    ),

    "ROA_Pct": rounded(
        net_profit / avg_assets * 100
    ),
    "ROE_Pct": rounded(
        profit_attributable / avg_shareholders_equity * 100
    ),

    "Opening_Balance_Source": previous["Source_Document"],
    "Opening_Balance_Source_PDF_Page": (
        previous["Source_PDF_Page"]
    ),

    "ROA_Method": "Net profit / average total assets * 100",
    "ROE_Method": (
        "(Net profit - Tier 1 coupon) / average ordinary "
        "shareholders equity * 100; ordinary shareholders "
        "equity excludes Tier 1 capital notes"
    ),

    "NIM_Pct": 1.92,
    "NIM_Source_Document": "nbad-2016-annual-report-eng.pdf",
    "NIM_Source_PDF_Page": 41,
    "NIM_Method": (
        "Published annualised NIM based on daily average "
        "performing assets"
    ),
})

assert set(record) == set(columns)
assert record["Year"] == "2016"
assert len(rows) + 1 == 7

# Build and validate the new CSV before replacing the original.
output = io.StringIO(newline="")
writer = csv.DictWriter(output, fieldnames=columns)
writer.writeheader()
writer.writerows(rows + [record])

new_bytes = output.getvalue().encode("utf-8")
check_rows = list(csv.DictReader(
    io.StringIO(new_bytes.decode("utf-8"))
))

assert len(check_rows) == 7
assert check_rows[:6] == rows
assert check_rows[-1]["Year"] == "2016"

# Only write after all checks have passed.
CSV_PATH.write_bytes(new_bytes)

print("NBAD 2016 added successfully.")
print("Total records:", len(check_rows))
print("Total columns:", len(columns))
print("Years:", [r["Year"] for r in check_rows])
print("Historical records unchanged:", check_rows[:6] == rows)
print("ROA:", record["ROA_Pct"], "%")
print("ROE:", record["ROE_Pct"], "%")
print("CIR:", record["CIR_Pct"], "%")
print("NIM:", record["NIM_Pct"], "%")
print("NPL ratio:", record["NPL_Ratio_Pct"], "%")
print("CAR:", record["CAR_Pct"], "%")
print("CSV:", CSV_PATH)
