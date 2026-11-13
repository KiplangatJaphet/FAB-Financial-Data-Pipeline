import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

DATASET = Path("output/NBK_raw_financial_data.csv")
BACKUP_DIR = Path("output/backups")
SOURCE = "NBK_2024_Annual_Report.pdf"

if not DATASET.exists():
    raise SystemExit(f"STOP: Dataset not found: {DATASET}")

df = pd.read_csv(DATASET)

text_columns = [
    "Bank_Name",
    "Country",
    "Reporting_Currency",
    "Reporting_Unit",
    "Source_Document",
    "Source_PDF_Page",
    "Source_Printed_Pages",
    "Entity_Basis_Note"
]

for column in text_columns:
    df[column] = df[column].astype("string")

if len(df.columns) != 58:
    raise SystemExit("STOP: Expected 58 columns.")

if len(df) != 15 or set(df["Year"]) != set(range(2010, 2025)):
    raise SystemExit("STOP: Unexpected year coverage.")

if not (df["Bank_Name"] == "National Bank of Kuwait").all():
    raise SystemExit("STOP: Unexpected bank name.")

# Figures verified from the 2024 annual report.
# All values below are converted from KD thousands
# into KWD millions.

data = {
    2024: {
        "Total_Assets_LCU_Millions": 40338.156,
        "Total_Liabilities_LCU_Millions": 35181.424,
        "Total_Equity_LCU_Millions": 5156.732,
        "Shareholders_Equity_LCU_Millions": 4112.328,
        "Net_Profit_LCU_Millions": 638.560,
        "Profit_Attributable_To_Shareholders_LCU_Millions": 600.122,
        "Total_Operating_Income_LCU_Millions": 1251.203,
        "Operating_Expenses_LCU_Millions": 467.966,
        "Net_Interest_Income_LCU_Millions": 980.059,
        "Net_Impairment_Charge_LCU_Millions": 86.464,
        "Loans_Advances_Islamic_Financing_LCU_Millions": 23707.609,
        "Customer_Accounts_Other_Deposits_LCU_Millions": 22866.205
    },
    2023: {
        "Total_Assets_LCU_Millions": 37664.991,
        "Total_Liabilities_LCU_Millions": 32758.416,
        "Total_Equity_LCU_Millions": 4906.575,
        "Shareholders_Equity_LCU_Millions": 3883.772,
        "Net_Profit_LCU_Millions": 588.373,
        "Profit_Attributable_To_Shareholders_LCU_Millions": 560.620,
        "Total_Operating_Income_LCU_Millions": 1166.767,
        "Operating_Expenses_LCU_Millions": 426.459,
        "Net_Interest_Income_LCU_Millions": 905.137,
        "Net_Impairment_Charge_LCU_Millions": 103.068,
        "Loans_Advances_Islamic_Financing_LCU_Millions": 22281.004,
        "Customer_Accounts_Other_Deposits_LCU_Millions": 21948.957
    }
}

# Confirm that existing values do not conflict.
for year, values in data.items():
    mask = df["Year"] == year

    if mask.sum() != 1:
        raise SystemExit(f"STOP: Invalid row count for {year}")

    for column, value in values.items():
        existing = df.loc[mask, column].iloc[0]

        if pd.notna(existing) and abs(float(existing) - value) > 0.000001:
            raise SystemExit(
                f"STOP: Conflict in {year}, {column}: "
                f"existing={existing}, new={value}"
            )

# Create backup before modifying the dataset.
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = BACKUP_DIR / f"NBK_before_2024_extraction_{timestamp}.csv"
shutil.copy2(DATASET, backup)

# Update verified fields.
for year, values in data.items():
    mask = df["Year"] == year

    for column, value in values.items():
        df.loc[mask, column] = value

    df.loc[mask, "Reporting_Currency"] = "KWD"
    df.loc[mask, "Reporting_Unit"] = "Millions"
    df.loc[mask, "Source_Document"] = SOURCE
    df.loc[mask, "Source_PDF_Page"] = "129;131"
    df.loc[mask, "Source_Printed_Pages"] = "125;127"
    df.loc[mask, "Entity_Basis_Note"] = (
        "NBK Group consolidated financial statements; "
        "2023 figures are comparatives from 2024 report; "
        "KD thousands converted to KWD millions; "
        "net interest income includes net Islamic financing income."
    )

# Validate accounting identity.
for year in data:
    row = df.loc[df["Year"] == year].iloc[0]

    assets = float(row["Total_Assets_LCU_Millions"])
    liabilities = float(row["Total_Liabilities_LCU_Millions"])
    equity = float(row["Total_Equity_LCU_Millions"])

    if abs(assets - liabilities - equity) > 0.001:
        raise SystemExit(
            f"STOP: Accounting identity failed for {year}"
        )

df.to_csv(DATASET, index=False, encoding="utf-8-sig")

print("\n========== NBK EXTRACTION COMPLETE ==========")
print("Dataset:", DATASET)
print("Backup:", backup)
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Years updated:", sorted(data))
print("Financial values processed:", sum(len(v) for v in data.values()))
print("Accounting identities: PASSED")
print("Other bank datasets: UNCHANGED")
print("=============================================")
