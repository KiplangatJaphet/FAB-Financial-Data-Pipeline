
from pathlib import Path
from datetime import datetime
import os
import shutil
import tempfile

import pandas as pd


# ============================================================
# 1. FILE PATHS
# ============================================================

CSV_PATH = Path("output/FAB_raw_financial_data.csv")
BACKUP_DIR = Path("output/backups")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)

if not CSV_PATH.exists():
    raise FileNotFoundError(
        f"Existing CSV not found: {CSV_PATH}"
    )


# ============================================================
# 2. LOAD AND VALIDATE EXISTING DATA
# ============================================================

df = pd.read_csv(CSV_PATH)

if len(df.columns) != 58:
    raise ValueError(
        f"Expected 58 columns, found {len(df.columns)}"
    )

required_columns = [
    "Bank_Name",
    "Country",
    "Year",
    "ROA_Pct",
    "ROE_Pct",
    "NPL_Ratio_Pct",
    "CAR_Pct",
    "CIR_Pct",
    "NIM_Pct",
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

df["Year"] = pd.to_numeric(
    df["Year"], errors="raise"
).astype(int)

if df["Year"].duplicated().any():
    raise ValueError(
        "Duplicate years found in existing CSV"
    )

if set(df["Year"]) != {2023, 2024}:
    raise ValueError(
        "Expected existing years 2023 and 2024. "
        f"Found: {sorted(df['Year'].tolist())}"
    )


# ============================================================
# 3. VERIFIED FAB 2022 FINANCIAL DATA
# All monetary amounts in AED millions
# ============================================================

financial_data = {

    "total_assets": 1110056.095,
    "total_liabilities": 995005.852,
    "total_equity": 115050.243,
    "shareholders_equity": 115037.783,

    "net_profit": 13422.111,
    "profit_before_tax": 14389.732,
    "profit_attributable": 13411.198,

    "operating_income": 20840.216,
    "operating_expenses": 6704.829,

    # Includes net income from Islamic financing products
    "net_interest_income": 14385.903,

    # Expense magnitude, stored as a positive amount
    "net_impairment_charge": 2839.358,

    "net_loans": 459593.327,
    "gross_loans": 479724.466,

    "customer_deposits": 700573.371,

    "stage3_exposure": 20898.190,
    "stage3_allowance": 9088.489,

    "regulatory_capital": 89267.500,

    # Tier 1 after deductions, including additional Tier 1
    "tier1_capital": 82856.749,
    "additional_tier1": 10754.750,
    "tier2_capital": 6410.751,

    "credit_rwa": 496035.297,
    "market_rwa": 42880.507,
    "operational_rwa": 32974.585,
    "total_rwa": 571890.389,

    # 2021 opening balances
    "previous_assets": 1001096.103,
    "previous_equity": 112647.431,
    "previous_shareholders_equity": 112632.003,
}


# ============================================================
# 4. CALCULATE FINANCIAL RATIOS
# ============================================================

average_assets = (
    financial_data["total_assets"]
    + financial_data["previous_assets"]
) / 2

average_equity = (
    financial_data["total_equity"]
    + financial_data["previous_equity"]
) / 2

average_shareholders_equity = (
    financial_data["shareholders_equity"]
    + financial_data["previous_shareholders_equity"]
) / 2

roa = (
    financial_data["net_profit"]
    / average_assets
) * 100

roe = (
    financial_data["profit_attributable"]
    / average_shareholders_equity
) * 100

cir = (
    financial_data["operating_expenses"]
    / financial_data["operating_income"]
) * 100

car = (
    financial_data["regulatory_capital"]
    / financial_data["total_rwa"]
) * 100

# Published ratios
published_npl = 3.90
published_nim = 1.59
published_car = 15.61


# ============================================================
# 5. CONSTRUCT 2022 RECORD
# ============================================================

# Start with all existing columns.
# Fields without verified values remain missing.
record = {
    column: pd.NA
    for column in df.columns
}

record.update({

    "Bank_Name": "First Abu Dhabi Bank",
    "Country": "United Arab Emirates",
    "Year": 2022,

    "Total_Assets_LCU_Millions":
        financial_data["total_assets"],

    "Total_Liabilities_LCU_Millions":
        financial_data["total_liabilities"],

    "Total_Equity_LCU_Millions":
        financial_data["total_equity"],

    "Shareholders_Equity_LCU_Millions":
        financial_data["shareholders_equity"],

    "Net_Profit_LCU_Millions":
        financial_data["net_profit"],

    "Profit_Before_Taxation_LCU_Millions":
        financial_data["profit_before_tax"],

    "Total_Operating_Income_LCU_Millions":
        financial_data["operating_income"],

    "Operating_Expenses_LCU_Millions":
        financial_data["operating_expenses"],

    "Net_Interest_Income_LCU_Millions":
        financial_data["net_interest_income"],

    "Net_Impairment_Charge_LCU_Millions":
        financial_data["net_impairment_charge"],

    "Loans_Advances_Islamic_Financing_LCU_Millions":
        financial_data["net_loans"],

    "Gross_Loans_LCU_Millions":
        financial_data["gross_loans"],

    "Customer_Accounts_Other_Deposits_LCU_Millions":
        financial_data["customer_deposits"],

    # Leave absolute NPL balance missing:
    # published NPL ratio is not equivalent to
    # Stage 3 plus POCI exposure.
    "Non_Performing_Loans_LCU_Millions": pd.NA,

    "Stage_3_Gross_Exposure_LCU_Millions":
        financial_data["stage3_exposure"],

    "Stage_3_Impairment_Allowance_LCU_Millions":
        financial_data["stage3_allowance"],

    "Total_Regulatory_Capital_LCU_Millions":
        financial_data["regulatory_capital"],

    "Eligible_Tier_1_Capital_LCU_Millions":
        financial_data["tier1_capital"],

    "Additional_Tier_1_Capital_LCU_Millions":
        financial_data["additional_tier1"],

    "Tier_2_Capital_LCU_Millions":
        financial_data["tier2_capital"],

    "Credit_Risk_RWA_LCU_Millions":
        financial_data["credit_rwa"],

    "Market_Risk_RWA_LCU_Millions":
        financial_data["market_rwa"],

    "Operational_Risk_RWA_LCU_Millions":
        financial_data["operational_rwa"],

    "RWA_LCU_Millions":
        financial_data["total_rwa"],

    "Published_CAR_Pct": published_car,

    "Reporting_Currency": "AED",
    "Reporting_Unit": "Millions",

    "Source_Document":
        "FAB_2022_Annual_Report.pdf; "
        "FAB_2022_Financial_Statements.pdf; "
        "FAB_2022_Pillar_3_Report.pdf",

    "Source_PDF_Page":
        "Annual Report: 82; Financial Statements: 9",

    "Source_Printed_Pages":
        "Annual Report: 162-163; "
        "Financial Statements: 8",

    "Gross_Loans_Source_PDF_Page":
        "FAB_2022_Financial_Statements.pdf: 84",

    "NPL_Source_PDF_Page":
        "FAB_2022_Annual_Report.pdf: 10",

    "Stage_3_Source_PDF_Pages":
        "FAB_2022_Financial_Statements.pdf: 84",

    "CAR_Source_PDF_Page":
        "FAB_2022_Pillar_3_Report.pdf: 30; "
        "FAB_2022_Financial_Statements.pdf: 116",

    "Entity_Basis_Note":
        "FAB consolidated group, post NBAD-FGB merger. "
        "NPL ratio is FAB-published; absolute NPL "
        "balance not independently established. "
        "CIR is calculated on operating income "
        "excluding exceptional Magnati disposal gain. "
        "Published adjusted CIR is 31.6%. "
        "Net interest income includes net Islamic "
        "financing income.",

    "NPL_Ratio_Pct": published_npl,
    "CAR_Pct": round(car, 2),
    "CIR_Pct": round(cir, 2),

    "Previous_Year_Total_Assets_LCU_Millions":
        financial_data["previous_assets"],

    "Previous_Year_Total_Equity_LCU_Millions":
        financial_data["previous_equity"],

    "Previous_Year_Shareholders_Equity_LCU_Millions":
        financial_data["previous_shareholders_equity"],

    "Average_Total_Assets_LCU_Millions":
        average_assets,

    "Average_Total_Equity_LCU_Millions":
        average_equity,

    "Average_Shareholders_Equity_LCU_Millions":
        average_shareholders_equity,

    "Profit_Attributable_To_Shareholders_LCU_Millions":
        financial_data["profit_attributable"],

    "ROA_Pct": round(roa, 2),
    "ROE_Pct": round(roe, 2),

    "Opening_Balance_Source":
        "FAB_2022_Annual_Report.pdf",

    "Opening_Balance_Source_PDF_Page": 82,

    "ROA_Method":
        "Net profit / average total assets * 100",

    "ROE_Method":
        "Profit attributable to shareholders / "
        "average shareholders equity * 100",

    "NIM_Pct": published_nim,

    "NIM_Source_Document":
        "FAB_2023_Annual_Report.pdf",

    "NIM_Source_PDF_Page": 14,

    "NIM_Method":
        "Published by FAB as 2022 comparative "
        "in 2023 Annual Report",

})


# ============================================================
# 6. APPEND RECORD AND SORT
# ============================================================

new_row = pd.DataFrame(
    [record],
    columns=df.columns
)

updated = pd.concat(
    [df, new_row],
    ignore_index=True
)

updated = updated.sort_values(
    "Year"
).reset_index(drop=True)


# ============================================================
# 7. VALIDATE BEFORE SAVING
# ============================================================

if len(updated) != 3:
    raise ValueError("Expected exactly 3 records")

if len(updated.columns) != 58:
    raise ValueError("Column count changed")

if updated["Year"].tolist() != [2022, 2023, 2024]:
    raise ValueError("Incorrect year sequence")

if updated["Year"].duplicated().any():
    raise ValueError("Duplicate year detected")

# Confirm old records have not changed.
for year in [2023, 2024]:

    original = df.loc[
        df["Year"] == year
    ].iloc[0]

    current = updated.loc[
        updated["Year"] == year
    ].iloc[0]

    if not original.equals(current):
        raise ValueError(
            f"Existing {year} record was modified"
        )

# Balance sheet check
assets = financial_data["total_assets"]
liabilities = financial_data["total_liabilities"]
equity = financial_data["total_equity"]

if abs(assets - liabilities - equity) > 0.01:
    raise ValueError(
        "2022 balance sheet does not balance"
    )

# Regulatory capital check
if abs(car - published_car) > 0.02:
    raise ValueError(
        "Calculated CAR differs from published CAR"
    )

# Validate ratios
expected_ratios = {
    "ROA_Pct": 1.27,
    "ROE_Pct": 11.78,
    "NPL_Ratio_Pct": 3.90,
    "CAR_Pct": 15.61,
    "CIR_Pct": 32.17,
    "NIM_Pct": 1.59,
}

row_2022 = updated.loc[
    updated["Year"] == 2022
].iloc[0]

for column, expected in expected_ratios.items():

    actual = float(row_2022[column])

    if abs(actual - expected) > 0.01:
        raise ValueError(
            f"{column}: expected {expected}, "
            f"found {actual}"
        )


# ============================================================
# 8. BACK UP AND SAVE ATOMICALLY
# ============================================================

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_path = BACKUP_DIR / (
    f"FAB_before_2022_{timestamp}.csv"
)

shutil.copy2(CSV_PATH, backup_path)

temporary_path = None

try:
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        prefix="FAB_2022_",
        dir=CSV_PATH.parent,
        delete=False,
        encoding="utf-8",
        newline=""
    ) as temporary_file:

        temporary_path = Path(temporary_file.name)

        updated.to_csv(
            temporary_file,
            index=False
        )

    # Verify the saved temporary CSV
    check = pd.read_csv(temporary_path)

    if check.shape != (3, 58):
        raise ValueError(
            "Saved CSV validation failed"
        )

    if check["Year"].tolist() != [2022, 2023, 2024]:
        raise ValueError(
            "Saved CSV years are incorrect"
        )

    # Replace only after all checks pass
    os.replace(temporary_path, CSV_PATH)

except Exception:
    if temporary_path and temporary_path.exists():
        temporary_path.unlink()
    raise


# ============================================================
# 9. DISPLAY FINAL RESULTS
# ============================================================

display_columns = [
    "Year",
    "ROA_Pct",
    "ROE_Pct",
    "NPL_Ratio_Pct",
    "CAR_Pct",
    "CIR_Pct",
    "NIM_Pct",
]

print("\n" + "=" * 75)
print("FAB FINANCIAL INDICATORS - 2022 TO 2024")
print("=" * 75)

print(
    updated[display_columns].to_string(
        index=False
    )
)

print("\nALL VALIDATION CHECKS PASSED.")

print("\nEXPORT COMPLETED SUCCESSFULLY")
print(f"Updated CSV: {CSV_PATH}")
print(f"Backup CSV: {backup_path}")
print(f"Total records: {len(updated)}")
print(f"Total columns: {len(updated.columns)}")
