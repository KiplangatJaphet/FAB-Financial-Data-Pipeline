
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

input_file = Path("output/FAB_raw_financial_data.csv")
backup_file = Path("output/FAB_raw_financial_data_backup.csv")

if not input_file.exists():
    raise FileNotFoundError(f"CSV not found: {input_file}")

# --------------------------------------------------
# 2. READ EXISTING DATA
# --------------------------------------------------

df = pd.read_csv(input_file)

df["Year"] = pd.to_numeric(df["Year"], errors="raise")

required_columns = [
    "Year",
    "Total_Assets_LCU_Millions",
    "Total_Equity_LCU_Millions",
    "Shareholders_Equity_LCU_Millions",
    "Net_Profit_LCU_Millions",
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

if set(df["Year"]) != {2023, 2024}:
    raise ValueError(
        "Expected exactly the 2023 and 2024 FAB records."
    )

if df["Year"].duplicated().any():
    raise ValueError("Duplicate years found.")

# --------------------------------------------------
# 3. VERIFIED 2022 OPENING BALANCES
# Source: FAB 2023 Annual Report
# PDF page 99, printed page 196
# Converted from AED thousands to AED millions
# --------------------------------------------------

opening_2022 = {
    "Total_Assets": 1110056.095,
    "Total_Equity": 115050.243,
    "Shareholders_Equity": 115037.783,
}

# Profit attributable to shareholders
# AED millions
shareholder_profit = {
    2023: 16405.493,
    2024: 17055.0,
}

# --------------------------------------------------
# 4. BUILD PREVIOUS-YEAR BALANCES
# --------------------------------------------------

df = df.sort_values("Year").reset_index(drop=True)

previous_assets = []
previous_equity = []
previous_shareholder_equity = []

for _, row in df.iterrows():

    year = int(row["Year"])

    if year == 2023:

        previous_assets.append(
            opening_2022["Total_Assets"]
        )

        previous_equity.append(
            opening_2022["Total_Equity"]
        )

        previous_shareholder_equity.append(
            opening_2022["Shareholders_Equity"]
        )

    else:

        previous_row = df.loc[
            df["Year"] == year - 1
        ]

        if previous_row.empty:
            raise ValueError(
                f"Missing opening balances for {year}"
            )

        previous_assets.append(
            float(
                previous_row[
                    "Total_Assets_LCU_Millions"
                ].iloc[0]
            )
        )

        previous_equity.append(
            float(
                previous_row[
                    "Total_Equity_LCU_Millions"
                ].iloc[0]
            )
        )

        previous_shareholder_equity.append(
            float(
                previous_row[
                    "Shareholders_Equity_LCU_Millions"
                ].iloc[0]
            )
        )

df["Previous_Year_Total_Assets_LCU_Millions"] = (
    previous_assets
)

df["Previous_Year_Total_Equity_LCU_Millions"] = (
    previous_equity
)

df["Previous_Year_Shareholders_Equity_LCU_Millions"] = (
    previous_shareholder_equity
)

# --------------------------------------------------
# 5. AVERAGE BALANCES
# --------------------------------------------------

df["Average_Total_Assets_LCU_Millions"] = (
    (
        df["Previous_Year_Total_Assets_LCU_Millions"]
        + df["Total_Assets_LCU_Millions"]
    ) / 2
)

df["Average_Total_Equity_LCU_Millions"] = (
    (
        df["Previous_Year_Total_Equity_LCU_Millions"]
        + df["Total_Equity_LCU_Millions"]
    ) / 2
)

df["Average_Shareholders_Equity_LCU_Millions"] = (
    (
        df["Previous_Year_Shareholders_Equity_LCU_Millions"]
        + df["Shareholders_Equity_LCU_Millions"]
    ) / 2
)

# --------------------------------------------------
# 6. PROFIT ATTRIBUTABLE TO SHAREHOLDERS
# --------------------------------------------------

df["Profit_Attributable_To_Shareholders_LCU_Millions"] = (
    df["Year"].map(shareholder_profit)
)

# --------------------------------------------------
# 7. CALCULATE ROA AND ROE
# --------------------------------------------------

df["ROA_Pct"] = (
    df["Net_Profit_LCU_Millions"]
    / df["Average_Total_Assets_LCU_Millions"]
    * 100
).round(2)

df["ROE_Pct"] = (
    df["Profit_Attributable_To_Shareholders_LCU_Millions"]
    / df["Average_Shareholders_Equity_LCU_Millions"]
    * 100
).round(2)

# --------------------------------------------------
# 8. SOURCE AUDIT TRAIL
# --------------------------------------------------

df["Opening_Balance_Source"] = df["Year"].map({
    2023: "FAB_2023_Annual_Report.pdf",
    2024: "FAB_2024_Annual_Report.pdf",
})

df["Opening_Balance_Source_PDF_Page"] = df["Year"].map({
    2023: 99,
    2024: 111,
})

df["ROA_Method"] = (
    "Net profit / average total assets * 100"
)

df["ROE_Method"] = (
    "Profit attributable to shareholders / "
    "average shareholders equity * 100"
)

# --------------------------------------------------
# 9. VALIDATION
# --------------------------------------------------

numeric_columns = [
    "ROA_Pct",
    "ROE_Pct",
    "Average_Total_Assets_LCU_Millions",
    "Average_Shareholders_Equity_LCU_Millions",
]

if df[numeric_columns].isna().any().any():
    raise ValueError(
        "Missing profitability calculation values."
    )

if (
    df["Average_Total_Assets_LCU_Millions"] <= 0
).any():
    raise ValueError("Invalid average assets.")

if (
    df["Average_Shareholders_Equity_LCU_Millions"] <= 0
).any():
    raise ValueError("Invalid average equity.")

print("\n" + "=" * 65)
print("FAB PROFITABILITY RATIOS")
print("=" * 65)

print(
    df[
        [
            "Year",
            "ROA_Pct",
            "ROE_Pct",
            "NPL_Ratio_Pct",
            "CAR_Pct",
            "CIR_Pct",
        ]
    ].to_string(index=False)
)

print("\nVALIDATION PASSED.")

# --------------------------------------------------
# 10. BACKUP AND EXPORT
# --------------------------------------------------

# Write the updated dataset to a temporary file first.
# This prevents overwriting the original before
# the new CSV has been successfully generated.

temporary_file = input_file.with_suffix(".tmp")

try:
    df.to_csv(
        temporary_file,
        index=False,
        encoding="utf-8-sig"
    )

    # Preserve the previous version.
    import shutil
    shutil.copy2(input_file, backup_file)

    # Replace the original CSV.
    temporary_file.replace(input_file)

except PermissionError:
    print(
        "\nPERMISSION ERROR: Close the CSV in Excel "
        "and run the script again."
    )
    raise

print("\nEXPORT COMPLETED SUCCESSFULLY")
print(f"Updated CSV: {input_file}")
print(f"Backup CSV: {backup_file}")
print(f"Total records: {len(df)}")
print(f"Total columns: {len(df.columns)}")
