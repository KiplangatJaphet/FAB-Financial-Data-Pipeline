
from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd

# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

csv_file = Path("output/FAB_raw_financial_data.csv")
backup_dir = Path("output/backups")
temporary_file = Path("output/FAB_raw_financial_data.tmp")

if not csv_file.exists():
    raise FileNotFoundError(f"CSV not found: {csv_file}")

# --------------------------------------------------
# 2. LOAD AND VALIDATE EXISTING DATA
# --------------------------------------------------

df = pd.read_csv(csv_file)

if len(df.columns) != 58:
    raise ValueError(
        f"Expected 58 columns, found {len(df.columns)}"
    )

if "Year" not in df.columns:
    raise ValueError("Year column is missing.")

df["Year"] = pd.to_numeric(
    df["Year"], errors="raise"
).astype(int)

if len(df) != 4 or set(df["Year"]) != {
    2021, 2022, 2023, 2024
}:
    raise ValueError(
        "Expected exactly four records: 2021–2024."
    )

if df["Year"].duplicated().any():
    raise ValueError("Duplicate years found.")

original_columns = df.columns.tolist()

# --------------------------------------------------
# 3. VERIFIED 2020 FINANCIAL DATA
# All monetary values in AED millions
# --------------------------------------------------

record = {column: None for column in original_columns}

record.update({
    "Bank_Name": "First Abu Dhabi Bank",
    "Country": "United Arab Emirates",
    "Year": 2020,

    "Total_Assets_LCU_Millions": 919060.532,
    "Total_Liabilities_LCU_Millions": 810021.540,
    "Total_Equity_LCU_Millions": 109038.992,
    "Shareholders_Equity_LCU_Millions": 108674.667,

    "Net_Profit_LCU_Millions": 10552.508,
    "Profit_Before_Taxation_LCU_Millions": 10893.706,
    "Total_Operating_Income_LCU_Millions": 18573.911,
    "Operating_Expenses_LCU_Millions": 5060.265,
    "Net_Interest_Income_LCU_Millions": 12256.479,
    "Net_Impairment_Charge_LCU_Millions": 2619.940,

    "Loans_Advances_Islamic_Financing_LCU_Millions": 386643.996,
    "Gross_Loans_LCU_Millions": 403288.746,
    "Customer_Accounts_Other_Deposits_LCU_Millions": 540882.472,

    # Published NPL amount is rounded to AED 15.8 billion.
    # Keep the exact-value field blank.
    "Non_Performing_Loans_LCU_Millions": None,

    # Stage 3 excludes the separately reported POCI category.
    "Stage_3_Gross_Exposure_LCU_Millions": 15166.539,
    "Stage_3_Impairment_Allowance_LCU_Millions": 6013.657,

    # Regulatory capital: FAB 2020 Pillar 3
    "Total_Regulatory_Capital_LCU_Millions": 83560.365,
    "Eligible_Tier_1_Capital_LCU_Millions": 77763.070,
    "Additional_Tier_1_Capital_LCU_Millions": 10754.750,
    "Tier_2_Capital_LCU_Millions": 5797.295,

    "Credit_Risk_RWA_LCU_Millions": 441184.990,
    "Market_Risk_RWA_LCU_Millions": 28419.038,
    "Operational_Risk_RWA_LCU_Millions": 35735.719,
    "RWA_LCU_Millions": 505339.747,

    "Published_CAR_Pct": 16.54,
    "NPL_Ratio_Pct": 3.97,
    "CAR_Pct": 16.54,

    "Reporting_Currency": "AED",
    "Reporting_Unit": "Millions",

    # Source documentation
    "Source_Document": (
        "FAB_2020_Financial_Statements.pdf; "
        "FAB_2020_Annual_Report.pdf; "
        "FAB_2020_Pillar_3_Report.pdf"
    ),
    "Source_PDF_Page": (
        "Financial Statements: 12-13"
    ),
    "Source_Printed_Pages": (
        "Financial Statements: 9-10"
    ),
    "Gross_Loans_Source_PDF_Page": (
        "FAB_2020_Financial_Statements.pdf: 96"
    ),
    "NPL_Source_PDF_Page": (
        "FAB_2020_Annual_Report.pdf: 6, 16"
    ),
    "Stage_3_Source_PDF_Pages": (
        "FAB_2020_Financial_Statements.pdf: 96"
    ),
    "CAR_Source_PDF_Page": (
        "FAB_2020_Pillar_3_Report.pdf: 15-16"
    ),

    "Entity_Basis_Note": (
        "FAB consolidated group, post NBAD-FGB merger. "
        "Financial amounts are sourced from the original "
        "audited 2020 financial statements. "
        "Gross loans and Stage 3 exposures are sourced "
        "from Note 43, credit quality analysis. "
        "Purchased or originated credit-impaired (POCI) "
        "loans are disclosed separately from Stage 3. "
        "The published NPL ratio is 3.97%; the absolute "
        "NPL amount is omitted because the annual report "
        "provides a rounded figure of AED 15.8 billion. "
        "Regulatory capital and RWA are sourced from "
        "2020 Pillar 3 disclosures. "
        "Published NIM has not yet been verified."
    ),

    # 2019 opening balances
    "Previous_Year_Total_Assets_LCU_Millions": 821968.015,
    "Previous_Year_Total_Equity_LCU_Millions": 108037.036,
    "Previous_Year_Shareholders_Equity_LCU_Millions": 107606.562,

    "Profit_Attributable_To_Shareholders_LCU_Millions": 10555.229,

    "Opening_Balance_Source": (
        "FAB_2020_Financial_Statements.pdf"
    ),
    "Opening_Balance_Source_PDF_Page": 12,

    "ROA_Method": (
        "Net profit / average total assets * 100"
    ),
    "ROE_Method": (
        "Profit attributable to shareholders / "
        "average shareholders equity * 100"
    ),

    # Published NIM not yet verified
    "NIM_Pct": None,
    "NIM_Source_Document": None,
    "NIM_Source_PDF_Page": None,
    "NIM_Method": "Published NIM not yet verified",
})

# --------------------------------------------------
# 4. CALCULATE AVERAGE BALANCES
# --------------------------------------------------

record["Average_Total_Assets_LCU_Millions"] = (
    record["Previous_Year_Total_Assets_LCU_Millions"]
    + record["Total_Assets_LCU_Millions"]
) / 2

record["Average_Total_Equity_LCU_Millions"] = (
    record["Previous_Year_Total_Equity_LCU_Millions"]
    + record["Total_Equity_LCU_Millions"]
) / 2

record["Average_Shareholders_Equity_LCU_Millions"] = (
    record["Previous_Year_Shareholders_Equity_LCU_Millions"]
    + record["Shareholders_Equity_LCU_Millions"]
) / 2

# --------------------------------------------------
# 5. CALCULATE FINANCIAL RATIOS
# --------------------------------------------------

record["ROA_Pct"] = round(
    record["Net_Profit_LCU_Millions"]
    / record["Average_Total_Assets_LCU_Millions"]
    * 100, 2
)

record["ROE_Pct"] = round(
    record["Profit_Attributable_To_Shareholders_LCU_Millions"]
    / record["Average_Shareholders_Equity_LCU_Millions"]
    * 100, 2
)

record["CIR_Pct"] = round(
    record["Operating_Expenses_LCU_Millions"]
    / record["Total_Operating_Income_LCU_Millions"]
    * 100, 2
)

# --------------------------------------------------
# 6. VALIDATE THE 2020 RECORD
# --------------------------------------------------

def check_close(actual, expected, label, tolerance=0.01):
    if abs(actual - expected) > tolerance:
        raise ValueError(
            f"{label}: expected {expected}, found {actual}"
        )

check_close(
    record["Total_Liabilities_LCU_Millions"]
    + record["Total_Equity_LCU_Millions"],
    record["Total_Assets_LCU_Millions"],
    "Balance sheet"
)

check_close(
    record["Credit_Risk_RWA_LCU_Millions"]
    + record["Market_Risk_RWA_LCU_Millions"]
    + record["Operational_Risk_RWA_LCU_Millions"],
    record["RWA_LCU_Millions"],
    "Total RWA"
)

check_close(
    record["Eligible_Tier_1_Capital_LCU_Millions"]
    + record["Tier_2_Capital_LCU_Millions"],
    record["Total_Regulatory_Capital_LCU_Millions"],
    "Total regulatory capital"
)

check_close(record["ROA_Pct"], 1.21, "ROA")
check_close(record["ROE_Pct"], 9.76, "ROE")
check_close(record["CIR_Pct"], 27.24, "CIR")

calculated_car = round(
    record["Total_Regulatory_Capital_LCU_Millions"]
    / record["RWA_LCU_Millions"]
    * 100, 2
)

check_close(calculated_car, 16.54, "CAR")

# Validate gross loan exposure components
check_close(
    362778.965 + 20275.910 + 15166.539 + 5067.332,
    record["Gross_Loans_LCU_Millions"],
    "Gross loans reconciliation"
)

# --------------------------------------------------
# 7. APPEND WITHOUT ALTERING EXISTING RECORDS
# --------------------------------------------------

new_row = pd.DataFrame(
    [record],
    columns=original_columns
)

updated = pd.concat(
    [df, new_row],
    ignore_index=True
)

updated = updated.sort_values(
    "Year"
).reset_index(drop=True)

if len(updated) != 5:
    raise ValueError("Expected five records.")

if set(updated["Year"]) != {
    2020, 2021, 2022, 2023, 2024
}:
    raise ValueError("Unexpected year coverage.")

if updated["Year"].duplicated().any():
    raise ValueError("Duplicate years after insertion.")

# Verify existing records remain unchanged
existing_after = updated[
    updated["Year"] >= 2021
].reset_index(drop=True)

pd.testing.assert_frame_equal(
    df.sort_values("Year").reset_index(drop=True),
    existing_after,
    check_dtype=False
)

# --------------------------------------------------
# 8. PREVIEW BEFORE SAVING
# --------------------------------------------------

print("\n" + "=" * 75)
print("FAB FINANCIAL DATA: 2020-2024")
print("=" * 75)

preview_columns = [
    "Year",
    "Total_Assets_LCU_Millions",
    "Net_Profit_LCU_Millions",
    "ROA_Pct",
    "ROE_Pct",
    "NPL_Ratio_Pct",
    "CAR_Pct",
    "CIR_Pct",
    "NIM_Pct",
]

print(
    updated[preview_columns].to_string(index=False)
)

print("\nVALIDATION PASSED.")
print("Existing 2021-2024 records preserved.")

# --------------------------------------------------
# 9. BACKUP AND SAVE
# --------------------------------------------------

backup_dir.mkdir(
    parents=True,
    exist_ok=True
)

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S_%f"
)

backup_file = backup_dir / (
    f"FAB_before_2020_insertion_{timestamp}.csv"
)

if temporary_file.exists():
    raise FileExistsError(
        f"Temporary file already exists: {temporary_file}"
    )

try:
    updated.to_csv(
        temporary_file,
        index=False,
        encoding="utf-8-sig"
    )

    # Backup existing four-year dataset first.
    shutil.copy2(
        csv_file,
        backup_file
    )

    # Replace only after backup succeeds.
    temporary_file.replace(csv_file)

except Exception:
    if temporary_file.exists():
        temporary_file.unlink()
    raise

print("\nEXPORT COMPLETED SUCCESSFULLY")
print(f"Updated CSV: {csv_file}")
print(f"Backup CSV: {backup_file}")
print(f"Total records: {len(updated)}")
print(f"Total columns: {len(updated.columns)}")
