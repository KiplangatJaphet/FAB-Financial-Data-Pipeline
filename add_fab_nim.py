
from pathlib import Path
import pandas as pd
import shutil

# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

csv_file = Path("output/FAB_raw_financial_data.csv")
backup_file = Path("output/FAB_before_NIM_backup.csv")
temporary_file = Path("output/FAB_raw_financial_data.tmp")

if not csv_file.exists():
    raise FileNotFoundError(f"File not found: {csv_file}")

# --------------------------------------------------
# 2. LOAD EXISTING DATA
# --------------------------------------------------

df = pd.read_csv(csv_file)

if "Year" not in df.columns:
    raise ValueError("Year column is missing.")

df["Year"] = pd.to_numeric(
    df["Year"], errors="raise"
).astype(int)

if len(df) != 2 or set(df["Year"]) != {2023, 2024}:
    raise ValueError(
        "Expected exactly two records: 2023 and 2024."
    )

if df["Year"].duplicated().any():
    raise ValueError("Duplicate year records found.")

# --------------------------------------------------
# 3. VERIFIED FAB NIM DATA
# --------------------------------------------------

nim_data = {
    2023: {
        "nim": 1.80,
        "source": "FAB_2023_Annual_Report.pdf",
        "page": 14,
    },
    2024: {
        "nim": 1.93,
        "source": "FAB_2024_Annual_Report.pdf",
        "page": 14,
    },
}

df["NIM_Pct"] = df["Year"].map(
    lambda year: nim_data[year]["nim"]
)

df["NIM_Source_Document"] = df["Year"].map(
    lambda year: nim_data[year]["source"]
)

df["NIM_Source_PDF_Page"] = df["Year"].map(
    lambda year: nim_data[year]["page"]
)

df["NIM_Method"] = "Published by FAB"

# --------------------------------------------------
# 4. VALIDATE
# --------------------------------------------------

required_ratios = [
    "ROA_Pct",
    "ROE_Pct",
    "NPL_Ratio_Pct",
    "CAR_Pct",
    "CIR_Pct",
    "NIM_Pct",
]

missing_columns = [
    column for column in required_ratios
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing ratio columns: {missing_columns}"
    )

if df[required_ratios].isna().any().any():
    raise ValueError("Missing financial ratio values.")

if not df["NIM_Pct"].between(0, 100).all():
    raise ValueError("Invalid NIM percentage.")

df = df.sort_values("Year").reset_index(drop=True)

print("\n" + "=" * 70)
print("FAB FINANCIAL INDICATORS - 2023 AND 2024")
print("=" * 70)

print(
    df[
        ["Year"] + required_ratios
    ].to_string(index=False)
)

print("\nALL VALIDATION CHECKS PASSED.")

# --------------------------------------------------
# 5. BACKUP AND EXPORT
# --------------------------------------------------

try:
    df.to_csv(
        temporary_file,
        index=False,
        encoding="utf-8-sig"
    )

    shutil.copy2(csv_file, backup_file)

    temporary_file.replace(csv_file)

except PermissionError:
    print(
        "\nPERMISSION ERROR: Close the CSV in Excel "
        "and rerun the script."
    )
    raise

print("\nEXPORT COMPLETED SUCCESSFULLY")
print(f"Updated CSV: {csv_file}")
print(f"Backup CSV: {backup_file}")
print(f"Total records: {len(df)}")
print(f"Total columns: {len(df.columns)}")
