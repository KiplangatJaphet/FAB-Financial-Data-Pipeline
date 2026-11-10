import csv
from pathlib import Path

CSV_PATH = Path("output/NBAD_raw_financial_data.csv")

with CSV_PATH.open("r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames
    rows = list(reader)

assert columns is not None
assert len(columns) == 58, f"Expected 58 columns, found {len(columns)}"

if any(r["Year"] == "2014" for r in rows):
    raise SystemExit("NBAD 2014 already exists. No changes made.")

previous = next(r for r in rows if r["Year"] == "2013")

def previous_value(column):
    return float(previous[column])

def rounded(value):
    return round(value, 2)

assets = 376098.712
liabilities = 338135.330
equity = 37963.382
shareholders_equity = equity - 4000.000

net_profit = 5578.869
tier_1_coupon = 187.495
profit_attributable = net_profit - tier_1_coupon

operating_income = 10414.717
operating_expenses = 3696.033

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

assert round(assets - liabilities - equity, 6) == 0
assert round(37620.803 + 3398.196, 3) == 41018.999
assert round(
    209665.272 + 23611.281 + 16936.730, 3
) == 250213.283

record = {column: "" for column in columns}

record.update({
    "Bank_Name": "National Bank of Abu Dhabi",
    "Country": "United Arab Emirates",
    "Year": "2014",

    "Total_Assets_LCU_Millions": assets,
    "Total_Liabilities_LCU_Millions": liabilities,
    "Total_Equity_LCU_Millions": equity,
    "Shareholders_Equity_LCU_Millions": shareholders_equity,

    "Net_Profit_LCU_Millions": net_profit,
    "Profit_Before_Taxation_LCU_Millions": 5850.557,
    "Total_Operating_Income_LCU_Millions": operating_income,
    "Operating_Expenses_LCU_Millions": operating_expenses,
    "Net_Interest_Income_LCU_Millions": 6698.963,
    "Net_Impairment_Charge_LCU_Millions": 868.127,

    "Loans_Advances_Islamic_Financing_LCU_Millions": 194279.352,
    "Gross_Loans_LCU_Millions": 202072.325,
    "Customer_Accounts_Other_Deposits_LCU_Millions": 243184.652,
    "Non_Performing_Loans_LCU_Millions": 6160.000,

    "Total_Regulatory_Capital_LCU_Millions": 41018.999,
    "Eligible_Tier_1_Capital_LCU_Millions": 37620.803,
    "Tier_2_Capital_LCU_Millions": 3398.196,

    "Credit_Risk_RWA_LCU_Millions": 209665.272,
    "Market_Risk_RWA_LCU_Millions": 23611.281,
    "Operational_Risk_RWA_LCU_Millions": 16936.730,
    "RWA_LCU_Millions": 250213.283,

    "Published_CAR_Pct": 16.39,
    "Reporting_Currency": "AED",
    "Reporting_Unit": "Millions",

    "Source_Document": "nbad-2014-annual-report-eng.pdf",
    "Source_PDF_Page": "27-28",
    "Source_Printed_Pages": "3-4",
    "Gross_Loans_Source_PDF_Page": 79,
    "NPL_Source_PDF_Page": 12,
    "CAR_Source_PDF_Page": 70,

    "Entity_Basis_Note": (
        "NBAD consolidated financial statements; AED thousands "
        "converted to AED millions. "
        "Published NPL AED 6160 million and NPL ratio 3.07% "
        "from Financial Review PDF page 12. "
        "Alternative gross NPL disclosure AED 7285.355 million "
        "from PDF page 55; definitions not reconciled. "
        "Government of Abu Dhabi Tier 1 capital notes AED "
        "4000 million excluded from ordinary shareholders equity. "
        "Tier 1 coupon AED 187.495 million deducted from net "
        "profit for ROE; verified on PDF pages 30, 31 and 110. "
        "Published return on shareholders funds was 16.8% "
        "on PDF page 12; calculated ROE uses average ordinary "
        "shareholders equity. "
        "Published NIM 2.00% from PDF page 12. "
        "The 2014 report presents 2013 comparative total equity "
        "of AED 34671.391 million versus AED 34678.541 million "
        "in the existing 2013 dataset; comparative regulatory "
        "capital AED 37301.911 million versus AED 37309.062 "
        "million; comparative net profit AED 4743.555 million "
        "versus AED 4733.125 million. "
        "Original 2013 dataset values retained and used as "
        "opening balances for calculated returns. "
        "IFRS 9 Stage 3 fields not applicable to 2014."
    ),

    "NPL_Ratio_Pct": 3.07,
    "CAR_Pct": 16.39,
    "CIR_Pct": rounded(
        operating_expenses / operating_income * 100
    ),

    "Previous_Year_Total_Assets_LCU_Millions": prev_assets,
    "Previous_Year_Total_Equity_LCU_Millions": prev_equity,
    "Previous_Year_Shareholders_Equity_LCU_Millions": (
        prev_shareholders_equity
    ),

    "Average_Total_Assets_LCU_Millions": round(avg_assets, 3),
    "Average_Total_Equity_LCU_Millions": round(avg_equity, 3),
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
        "(Net profit - Tier 1 coupon) / average shareholders "
        "equity * 100; shareholders equity excludes Government "
        "Tier 1 capital notes"
    ),

    "NIM_Pct": 2.00,
    "NIM_Source_Document": "nbad-2014-annual-report-eng.pdf",
    "NIM_Source_PDF_Page": 12,
    "NIM_Method": "Published net interest margin",
})

rows.append(record)

with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

print("NBAD 2014 added successfully.")
print("Total records:", len(rows))
print("Years:", [r["Year"] for r in rows])
print("ROA:", record["ROA_Pct"], "%")
print("ROE:", record["ROE_Pct"], "%")
print("CIR:", record["CIR_Pct"], "%")
print("CSV:", CSV_PATH)
