
import pandas as pd
from pathlib import Path

# ============================================================
# 1. OUTPUT CONFIGURATION
# ============================================================

output_folder = Path("output")
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "FAB_raw_financial_data.csv"

source_document = "FAB_2024_Annual_Report.pdf"

entity_basis_note = (
    "Consolidated financial statements. "
    "2023 comparative figures are from the 2024 annual report. "
    "Note 51 describes presentation reclassifications of "
    "comparative interest income and interest expenses."
)

# ============================================================
# 2. FINANCIAL DATA
# ============================================================

data = [
    {
        "Bank_Name": "First Abu Dhabi Bank",
        "Country": "UAE",
        "Year": 2024,

        # Statement of financial position
        "Total_Assets_LCU_Millions": 1213247,
        "Total_Liabilities_LCU_Millions": 1082372,
        "Total_Equity_LCU_Millions": 130875,
        "Shareholders_Equity_LCU_Millions": 130752,

        # Income statement
        "Net_Profit_LCU_Millions": 17096,
        "Profit_Before_Taxation_LCU_Millions": 19914,
        "Total_Operating_Income_LCU_Millions": 31625,
        "Operating_Expenses_LCU_Millions": -7787,
        "Net_Interest_Income_LCU_Millions": 17474,
        "Net_Impairment_Charge_LCU_Millions": -3924,

        # Loans and deposits
        "Loans_Advances_Islamic_Financing_LCU_Millions": 528897,
        "Gross_Loans_LCU_Millions": 550513,
        "Customer_Accounts_Other_Deposits_LCU_Millions": 782379,

        # Credit risk
        "Non_Performing_Loans_LCU_Millions": 18514,
        "Stage_3_Gross_Exposure_LCU_Millions": 22677,
        "Stage_3_Impairment_Allowance_LCU_Millions": 9591,

        # Regulatory capital
        "Total_Regulatory_Capital_LCU_Millions": 111753,
        "Eligible_Tier_1_Capital_LCU_Millions": 109107,
        "Additional_Tier_1_Capital_LCU_Millions": 10755,
        "Tier_2_Capital_LCU_Millions": 13476,

        # Risk-weighted assets
        "Credit_Risk_RWA_LCU_Millions": 557331,
        "Market_Risk_RWA_LCU_Millions": 35614,
        "Operational_Risk_RWA_LCU_Millions": 46629,
        "RWA_LCU_Millions": 639574,

        # Published ratio
        "Published_CAR_Pct": 17.5,

        # Source metadata
        "Reporting_Currency": "AED",
        "Reporting_Unit": "Millions",
        "Source_Document": source_document,
        "Source_PDF_Page": 111,
        "Source_Printed_Pages": "220-221",
        "Gross_Loans_Source_PDF_Page": 135,
        "NPL_Source_PDF_Page": 164,
        "Stage_3_Source_PDF_Pages": "161-162; 167",
        "CAR_Source_PDF_Page": 178,
        "Entity_Basis_Note": entity_basis_note
    },

    {
        "Bank_Name": "First Abu Dhabi Bank",
        "Country": "UAE",
        "Year": 2023,

        # Statement of financial position
        "Total_Assets_LCU_Millions": 1168633,
        "Total_Liabilities_LCU_Millions": 1043210,
        "Total_Equity_LCU_Millions": 125423,
        "Shareholders_Equity_LCU_Millions": 125313,

        # Income statement
        "Net_Profit_LCU_Millions": 16510,
        "Profit_Before_Taxation_LCU_Millions": 17552,
        "Total_Operating_Income_LCU_Millions": 27471,
        "Operating_Expenses_LCU_Millions": -7125,
        "Net_Interest_Income_LCU_Millions": 16535,
        "Net_Impairment_Charge_LCU_Millions": -3078,

        # Loans and deposits
        "Loans_Advances_Islamic_Financing_LCU_Millions": 483954,
        "Gross_Loans_LCU_Millions": 504641,
        "Customer_Accounts_Other_Deposits_LCU_Millions": 759863,

        # Credit risk
        "Non_Performing_Loans_LCU_Millions": 19623,
        "Stage_3_Gross_Exposure_LCU_Millions": 22924,
        "Stage_3_Impairment_Allowance_LCU_Millions": 9923,

        # Regulatory capital
        "Total_Regulatory_Capital_LCU_Millions": 102299,
        "Eligible_Tier_1_Capital_LCU_Millions": 103732,
        "Additional_Tier_1_Capital_LCU_Millions": 10755,
        "Tier_2_Capital_LCU_Millions": 10313,

        # Risk-weighted assets
        "Credit_Risk_RWA_LCU_Millions": 513147,
        "Market_Risk_RWA_LCU_Millions": 36310,
        "Operational_Risk_RWA_LCU_Millions": 37992,
        "RWA_LCU_Millions": 587449,

        # Published ratio
        "Published_CAR_Pct": 17.4,

        # Source metadata
        "Reporting_Currency": "AED",
        "Reporting_Unit": "Millions",
        "Source_Document": source_document,
        "Source_PDF_Page": 111,
        "Source_Printed_Pages": "220-221",
        "Gross_Loans_Source_PDF_Page": 135,
        "NPL_Source_PDF_Page": 164,
        "Stage_3_Source_PDF_Pages": "161-162; 167",
        "CAR_Source_PDF_Page": 178,
        "Entity_Basis_Note": entity_basis_note
    }
]

# ============================================================
# 3. CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(data)

# ============================================================
# 4. CALCULATE FINANCIAL RATIOS
# ============================================================

# Non-Performing Loan Ratio
df["NPL_Ratio_Pct"] = (
    df["Non_Performing_Loans_LCU_Millions"]
    / df["Gross_Loans_LCU_Millions"]
    * 100
).round(2)

# Capital Adequacy Ratio
df["CAR_Pct"] = (
    df["Total_Regulatory_Capital_LCU_Millions"]
    / df["RWA_LCU_Millions"]
    * 100
).round(2)

# Cost-to-Income Ratio
# Expenses are negative in the financial statements.
# abs() converts them to positive amounts for this calculation.
df["CIR_Pct"] = (
    df["Operating_Expenses_LCU_Millions"].abs()
    / df["Total_Operating_Income_LCU_Millions"]
    * 100
).round(2)

# ============================================================
# 5. VALIDATE BALANCE SHEET
# ============================================================

df["Balance_Sheet_Check"] = (
    df["Total_Assets_LCU_Millions"]
    - df["Total_Liabilities_LCU_Millions"]
    - df["Total_Equity_LCU_Millions"]
)

# ============================================================
# 6. VALIDATE RISK-WEIGHTED ASSETS
# ============================================================

df["RWA_Check"] = (
    df["RWA_LCU_Millions"]
    - df["Credit_Risk_RWA_LCU_Millions"]
    - df["Market_Risk_RWA_LCU_Millions"]
    - df["Operational_Risk_RWA_LCU_Millions"]
)

# ============================================================
# 7. VALIDATE CAPITAL ADEQUACY RATIO
# ============================================================

df["CAR_Difference_Pct_Points"] = (
    df["CAR_Pct"] - df["Published_CAR_Pct"]
).round(2)

# ============================================================
# 8. DISPLAY VALIDATION RESULTS
# ============================================================

print("\n" + "=" * 70)
print("FAB FINANCIAL DATA VALIDATION")
print("=" * 70)

print("\nBALANCE SHEET CHECK")
print(
    df[
        [
            "Year",
            "Total_Assets_LCU_Millions",
            "Balance_Sheet_Check"
        ]
    ].to_string(index=False)
)

print("\nRISK-WEIGHTED ASSETS CHECK")
print(
    df[
        [
            "Year",
            "RWA_LCU_Millions",
            "RWA_Check"
        ]
    ].to_string(index=False)
)

print("\nFINANCIAL RATIOS CHECK")
print(
    df[
        [
            "Year",
            "NPL_Ratio_Pct",
            "CAR_Pct",
            "Published_CAR_Pct",
            "CIR_Pct"
        ]
    ].to_string(index=False)
)

print("\nMISSING VALUES")
print(df.isnull().sum())

# ============================================================
# 9. AUTOMATED VALIDATION
# ============================================================

assert (df["Balance_Sheet_Check"] == 0).all(), (
    "Balance sheet validation failed."
)

assert (df["RWA_Check"] == 0).all(), (
    "Risk-weighted assets validation failed."
)

assert (
    df["CAR_Difference_Pct_Points"].abs() <= 0.05
).all(), (
    "CAR does not reconcile with the published ratio."
)

assert (
    df["Total_Operating_Income_LCU_Millions"] > 0
).all(), (
    "Operating income must be positive for CIR calculation."
)

assert (
    df["Gross_Loans_LCU_Millions"] > 0
).all(), (
    "Gross loans must be positive."
)

assert not df[["Bank_Name", "Year"]].duplicated().any(), (
    "Duplicate bank-year records found."
)

assert not df.isnull().any().any(), (
    "Missing values detected."
)

print("\nALL VALIDATION CHECKS PASSED.")

# ============================================================
# 10. EXPORT TO CSV
# ============================================================

# Remove temporary validation columns.
validation_columns = [
    "Balance_Sheet_Check",
    "RWA_Check",
    "CAR_Difference_Pct_Points"
]

export_df = df.drop(columns=validation_columns)

export_df = export_df.sort_values(
    by=["Bank_Name", "Year"]
).reset_index(drop=True)

export_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print("\nEXPORT COMPLETED SUCCESSFULLY")
print(f"File saved to: {output_file}")
print(f"Total records: {len(export_df)}")
print(f"Total columns: {len(export_df.columns)}")
