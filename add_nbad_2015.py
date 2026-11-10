import csv
from pathlib import Path

CSV_PATH = Path("output/NBAD_raw_financial_data.csv")

with CSV_PATH.open("r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames
    rows = list(reader)

assert columns is not None
assert len(columns) == 58, f"Expected 58 columns, found {len(columns)}"

if any(r["Year"] == "2015" for r in rows):
    raise SystemExit("NBAD 2015 already exists. No changes made.")

previous = next(r for r in rows if r["Year"] == "2014")

def previous_value(column):
    return float(previous[column])

def rounded(value):
    return round(value, 2)

# Financial figures in AED millions
assets = 406563.807
liabilities = 363345.154
equity = 43218.653

tier_1_capital_notes = 6754.750
shareholders_equity = equity - tier_1_capital_notes

net_profit = 5231.817
tier_1_coupon = 201.187
profit_attributable = net_profit - tier_1_coupon

operating_income = 10555.850
operating_expenses = 4082.919

# Opening balances from the validated 2014 dataset
prev_assets = previous_value("Total_Assets_LCU_Millions")
prev_equity = previous_value("Total_Equity_LCU_Millions")
prev_shareholders_equity = previous_value(
    "Shareholders_Equity_LCU_Millions"
)

avg_assets = (assets + prev_assets) / 2
avg_equity = (equity + prev_equity) / 2
avg_shareholders_equity = (
    shareholders_equity + prev_shareholders_equity
) / 2

# Financial reconciliation checks
assert round(assets - liabilities - equity, 6) == 0
assert round(43098.202 + 2975.613, 3) == 46073.815
assert round(
    236976.736 + 20397.958 + 17883.226, 3
) == 275257.920
assert round(
    213075.191 - 1036.665 - 6124.973, 3
) == 205913.553

record = {column: "" for column in columns}

record.update({
    "Bank_Name": "National Bank of Abu Dhabi",
    "Country": "United Arab Emirates",
    "Year": "2015",

    "Total_Assets_LCU_Millions": assets,
    "Total_Liabilities_LCU_Millions": liabilities,
    "Total_Equity_LCU_Millions": equity,
    "Shareholders_Equity_LCU_Millions": shareholders_equity,

    "Net_Profit_LCU_Millions": net_profit,
    "Profit_Before_Taxation_LCU_Millions": 5529.960,
    "Total_Operating_Income_LCU_Millions": operating_income,
    "Operating_Expenses_LCU_Millions": operating_expenses,
    "Net_Interest_Income_LCU_Millions": 6944.085,
    "Net_Impairment_Charge_LCU_Millions": 942.971,

    "Loans_Advances_Islamic_Financing_LCU_Millions": 205913.553,
    "Gross_Loans_LCU_Millions": 213075.191,
    "Customer_Accounts_Other_Deposits_LCU_Millions": 233814.558,

    # Published approximate net NPL amount
    "Non_Performing_Loans_LCU_Millions": 5840.000,

    "Total_Regulatory_Capital_LCU_Millions": 46073.815,
    "Eligible_Tier_1_Capital_LCU_Millions": 43098.202,
    "Tier_2_Capital_LCU_Millions": 2975.613,

    "Credit_Risk_RWA_LCU_Millions": 236976.736,
    "Market_Risk_RWA_LCU_Millions": 20397.958,
    "Operational_Risk_RWA_LCU_Millions": 17883.226,
    "RWA_LCU_Millions": 275257.920,

    "Published_CAR_Pct": 16.74,
    "Reporting_Currency": "AED",
    "Reporting_Unit": "Millions",

    "Source_Document": "nbad-2015-annual-report-eng.pdf",
    "Source_PDF_Page": "48-49",
    "Source_Printed_Pages": "4-5",
    "Gross_Loans_Source_PDF_Page": 103,
    "NPL_Source_PDF_Page": 140,
    "CAR_Source_PDF_Page": 94,

    "Entity_Basis_Note": (
        "NBAD consolidated financial statements; AED thousands "
        "converted to AED millions. "
        "Balance sheet PDF page 48; profit or loss PDF page 49. "
        "Published approximate net NPL AED 5840 million and "
        "NPL ratio 2.76% from Financial Review PDF page 140. "
        "Exact gross non-performing loans AED 6883.308 million "
        "from PDF page 79; gross and net NPL definitions differ. "
        "Gross loans AED 213075.191 million from PDF page 103. "
        "Tier 1 capital notes AED 6754.750 million excluded "
        "from ordinary shareholders equity. "
        "Tier 1 coupon AED 201.187 million deducted from "
        "net profit for calculated ROE; verified in statements "
        "of changes in equity and cash flows on PDF pages 51-52. "
        "Published return on shareholders funds 14.3% "
        "from PDF page 42. "
        "Published NIM 1.97%, annualised using daily average "
        "performing assets, from PDF page 42. "
        "The 2015 report shows comparative 2014 NIM of 1.95% "
        "whereas the existing 2014 dataset uses 2.00% "
        "from the earlier report; original 2014 data retained. "
        "IFRS 9 Stage 3 fields not applicable to 2015."
    ),

    "NPL_Ratio_Pct": 2.76,
    "CAR_Pct": 16.74,

    "CIR_Pct": rounded(
        operating_expenses / operating_income * 100
    ),

    "Previous_Year_Total_Assets_LCU_Millions": prev_assets,
    "Previous_Year_Total_Equity_LCU_Millions": prev_equity,
    "Previous_Year_Shareholders_Equity_LCU_Millions": (
        prev_shareholders_equity
    ),

    "Average_Total_Assets_LCU_Millions": round(avg_assets, 4),
    "Average_Total_Equity_LCU_Millions": round(avg_equity, 4),
    "Average_Shareholders_Equity_LCU_Millions": round(
        avg_shareholders_equity, 4
    ),

    "Profit_Attributable_To_Shareholders_LCU_Millions": (
        profit_attributable
    ),

    "ROA_Pct": rounded(net_profit / avg_assets * 100),
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

    "NIM_Pct": 1.97,
    "NIM_Source_Document": "nbad-2015-annual-report-eng.pdf",
    "NIM_Source_PDF_Page": 42,
    "NIM_Method": (
        "Published annualised NIM based on daily average "
        "performing assets"
    ),
})

rows.append(record)

with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

print("NBAD 2015 added successfully.")
print("Total records:", len(rows))
print("Years:", [r["Year"] for r in rows])
print("ROA:", record["ROA_Pct"], "%")
print("ROE:", record["ROE_Pct"], "%")
print("CIR:", record["CIR_Pct"], "%")
print("NIM:", record["NIM_Pct"], "%")
print("CSV:", CSV_PATH)
