
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import pandas as pd
import os

CSV_PATH = Path("output/FAB_raw_financial_data.csv")
BACKUP_DIR = Path("output/backups")

EXPECTED_COLUMNS = 58
EXPECTED_EXISTING_YEARS = {2022, 2023, 2024}

FS = "FAB_2021_Financial_Statements.pdf"
AR = "FAB_2021_Annual_Report.pdf"
P3 = "FAB_2021_Pillar_3_Report.pdf"

def ratio(numerator, denominator):
    return round(numerator / denominator * 100, 2)

def check(condition, message):
    if not condition:
        raise ValueError(message)

# ------------------------------------------------------------
# 1. READ EXISTING DATA
# ------------------------------------------------------------

check(CSV_PATH.exists(), f"CSV not found: {CSV_PATH}")

df = pd.read_csv(CSV_PATH, dtype={"Bank_Name": str})

check(
    len(df.columns) == EXPECTED_COLUMNS,
    f"Expected 58 columns; found {len(df.columns)}"
)

check(
    "Year" in df.columns,
    "Missing Year column"
)

check(
    not df["Year"].isna().any(),
    "Missing year values"
)

existing_years = set(df["Year"].astype(int))

check(
    existing_years == EXPECTED_EXISTING_YEARS,
    f"Unexpected existing years: {existing_years}"
)

check(
    len(df) == 3,
    f"Expected 3 records; found {len(df)}"
)

check(
    not df["Year"].duplicated().any(),
    "Duplicate years found"
)

original = df.copy(deep=True)

# ------------------------------------------------------------
# 2. SOURCE VALUES - AED MILLIONS
# ------------------------------------------------------------

assets = 1000343.377
liabilities = 887513.804
equity = 112829.573
shareholders_equity = 112814.145

profit = 12542.272
shareholder_profit = 12531.111

operating_income = 21681.255
operating_expenses = 5836.474

previous_assets = 919060.532
previous_equity = 109038.992
previous_shareholders_equity = 108674.667

average_assets = (assets + previous_assets) / 2
average_equity = (equity + previous_equity) / 2
average_shareholders_equity = (
    shareholders_equity + previous_shareholders_equity
) / 2

roa = ratio(profit, average_assets)
roe = ratio(
    shareholder_profit,
    average_shareholders_equity
)
cir = ratio(operating_expenses, operating_income)

capital = 88982.629
rwa = 578995.264
car = ratio(capital, rwa)

# ------------------------------------------------------------
# 3. BUILD RECORD
# ------------------------------------------------------------

record = {column: None for column in df.columns}

values = {
    "Bank_Name": "First Abu Dhabi Bank",
    "Country": "United Arab Emirates",
    "Year": 2021,

    "Total_Assets_LCU_Millions": assets,
    "Total_Liabilities_LCU_Millions": liabilities,
    "Total_Equity_LCU_Millions": equity,
    "Shareholders_Equity_LCU_Millions": shareholders_equity,

    "Net_Profit_LCU_Millions": profit,
    "Profit_Before_Taxation_LCU_Millions": 13186.544,
    "Total_Operating_Income_LCU_Millions": operating_income,
    "Operating_Expenses_LCU_Millions": operating_expenses,
    "Net_Interest_Income_LCU_Millions": 11658.132,
    "Net_Impairment_Charge_LCU_Millions": 2658.237,

    "Loans_Advances_Islamic_Financing_LCU_Millions": 410154.614,
    "Gross_Loans_LCU_Millions": 428783.318,
    "Customer_Accounts_Other_Deposits_LCU_Millions": 614459.265,

    # Absolute NPL balance not available at exact precision.
    "Non_Performing_Loans_LCU_Millions": None,

    "Stage_3_Gross_Exposure_LCU_Millions": 16807.188,
    "Stage_3_Impairment_Allowance_LCU_Millions": 7358.566,

    "Total_Regulatory_Capital_LCU_Millions": capital,
    "Eligible_Tier_1_Capital_LCU_Millions": 93421.602,
    "Additional_Tier_1_Capital_LCU_Millions": 10754.750,
    "Tier_2_Capital_LCU_Millions": 6232.562,

    "Credit_Risk_RWA_LCU_Millions": 477057.405,
    "Market_Risk_RWA_LCU_Millions": 69423.094,
    "Operational_Risk_RWA_LCU_Millions": 32514.765,
    "RWA_LCU_Millions": rwa,

    "Published_CAR_Pct": 15.37,
    "Reporting_Currency": "AED",
    "Reporting_Unit": "Millions",

    "Source_Document": FS,
    "Source_PDF_Page": "9-10",
    "Source_Printed_Pages": "8-9",
    "Gross_Loans_Source_PDF_Page": 46,
    "NPL_Source_PDF_Page": 7,
    "Stage_3_Source_PDF_Pages": "90",
    "CAR_Source_PDF_Page": 29,

    "Entity_Basis_Note": (
        "FAB consolidated group; original audited 2021 "
        "financial statements. The 2022 financial statements "
        "subsequently restated 2021 comparative figures "
        "following the Bank Audi Egypt purchase price "
        "allocation exercise (2022 FS, PDF pages 127-128). "
        "2021 closing balances retain original reported "
        "amounts; 2022 opening balances retain restated "
        "comparatives. CAR sourced from 2021 Pillar 3. "
        "NPL ratio is published; absolute NPL balance omitted "
        "because the annual report gives a rounded amount."
    ),

    "NPL_Ratio_Pct": 4.00,
    "CAR_Pct": car,
    "CIR_Pct": cir,

    "Previous_Year_Total_Assets_LCU_Millions": previous_assets,
    "Previous_Year_Total_Equity_LCU_Millions": previous_equity,
    "Previous_Year_Shareholders_Equity_LCU_Millions":
        previous_shareholders_equity,

    "Average_Total_Assets_LCU_Millions": average_assets,
    "Average_Total_Equity_LCU_Millions": average_equity,
    "Average_Shareholders_Equity_LCU_Millions":
        average_shareholders_equity,

    "Profit_Attributable_To_Shareholders_LCU_Millions":
        shareholder_profit,

    "ROA_Pct": roa,
    "ROE_Pct": roe,

    "Opening_Balance_Source": FS,
    "Opening_Balance_Source_PDF_Page": 9,

    "ROA_Method": (
        "Net profit / average beginning and ending total assets"
    ),
    "ROE_Method": (
        "Profit attributable to shareholders / average "
        "beginning and ending shareholders equity"
    ),

    "NIM_Pct": 1.50,
    "NIM_Source_Document": AR,
    "NIM_Source_PDF_Page": 16,
    "NIM_Method": "Published net interest margin",
}

unknown = set(values) - set(df.columns)
check(not unknown, f"Unknown columns: {unknown}")

record.update(values)

new_row = pd.DataFrame([record], columns=df.columns)

updated = pd.concat(
    [df, new_row],
    ignore_index=True
)

updated = updated.sort_values(
    "Year"
).reset_index(drop=True)

# ------------------------------------------------------------
# 4. VALIDATION
# ------------------------------------------------------------

check(
    set(updated["Year"].astype(int)) ==
    {2021, 2022, 2023, 2024},
    "Incorrect years after insertion"
)

check(len(updated) == 4, "Expected 4 records")
check(len(updated.columns) == 58, "Expected 58 columns")
check(
    not updated["Year"].duplicated().any(),
    "Duplicate year found"
)

check(
    abs(assets - liabilities - equity) < 0.001,
    "Balance sheet does not balance"
)

check(
    abs(
        477057.405 + 69423.094 + 32514.765 - rwa
    ) < 0.001,
    "RWA components do not reconcile"
)

check(roa == 1.31, f"Unexpected ROA: {roa}")
check(roe == 11.32, f"Unexpected ROE: {roe}")
check(cir == 26.92, f"Unexpected CIR: {cir}")
check(car == 15.37, f"Unexpected CAR: {car}")

# Ensure existing rows have not changed.
retained = updated[
    updated["Year"].astype(int).isin(
        EXPECTED_EXISTING_YEARS
    )
].reset_index(drop=True)

pd.testing.assert_frame_equal(
    original.reset_index(drop=True),
    retained,
    check_dtype=False
)

# ------------------------------------------------------------
# 5. BACKUP AND ATOMIC EXPORT
# ------------------------------------------------------------

BACKUP_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = BACKUP_DIR / (
    f"FAB_before_2021_{timestamp}.csv"
)

temp_path = CSV_PATH.with_suffix(".tmp.csv")

try:
    # Backup existing CSV before making changes.
    import shutil
    shutil.copy2(CSV_PATH, backup_path)

    updated.to_csv(temp_path, index=False)

    # Re-read output before replacing original.
    verified = pd.read_csv(temp_path)

    check(len(verified) == 4, "Export validation failed")
    check(
        len(verified.columns) == 58,
        "Export column validation failed"
    )

    os.replace(temp_path, CSV_PATH)

finally:
    if temp_path.exists():
        temp_path.unlink()

# ------------------------------------------------------------
# 6. RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("FAB FINANCIAL INDICATORS - 2021 TO 2024")
print("=" * 75)

columns = [
    "Year",
    "ROA_Pct",
    "ROE_Pct",
    "NPL_Ratio_Pct",
    "CAR_Pct",
    "CIR_Pct",
    "NIM_Pct",
]

print(updated[columns].to_string(index=False))

print("\nALL VALIDATION CHECKS PASSED.")
print("\nEXPORT COMPLETED SUCCESSFULLY")
print(f"Updated CSV: {CSV_PATH}")
print(f"Backup CSV: {backup_path}")
print(f"Total records: {len(updated)}")
print(f"Total columns: {len(updated.columns)}")
