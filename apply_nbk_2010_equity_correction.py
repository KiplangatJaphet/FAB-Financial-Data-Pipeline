from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd

path = Path("output/NBK_raw_financial_data.csv")
backup_dir = Path("output/backups")
backup_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(path, low_memory=False)

if df.shape != (15, 58):
    raise SystemExit("STOP: Unexpected dataset dimensions.")

mask = df["Year"] == 2010

if mask.sum() != 1:
    raise SystemExit("STOP: Expected exactly one 2010 record.")

row = df.loc[mask].iloc[0]

expected_existing = {
    "Shareholders_Equity_LCU_Millions": 2074.0,
    "Total_Equity_LCU_Millions": None,
    "Total_Liabilities_LCU_Millions": None,
}

for field, expected in expected_existing.items():
    current = row[field]

    if expected is None:
        if pd.notna(current):
            raise SystemExit(f"STOP: {field} is no longer missing.")
    elif pd.isna(current) or abs(float(current) - expected) > 0.000001:
        raise SystemExit(f"STOP: Unexpected value in {field}.")

updates = {
    "Shareholders_Equity_LCU_Millions": 2217.635,
    "Total_Equity_LCU_Millions": 2230.503,
    "Total_Liabilities_LCU_Millions": 10668.397,
}

assets = float(row["Total_Assets_LCU_Millions"])

difference = assets - (
    updates["Total_Liabilities_LCU_Millions"]
    + updates["Total_Equity_LCU_Millions"]
)

if abs(difference) > 0.001:
    raise SystemExit("STOP: Accounting identity failed.")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = backup_dir / f"NBK_before_2010_equity_correction_{timestamp}.csv"

shutil.copy2(path, backup)

for field, value in updates.items():
    df.loc[mask, field] = value

df.to_csv(path, index=False)

check = pd.read_csv(path, low_memory=False)
r = check.loc[check["Year"] == 2010].iloc[0]

for field, expected in updates.items():
    if abs(float(r[field]) - expected) > 0.000001:
        raise SystemExit(f"STOP: Verification failed for {field}")

print("\n========== NBK 2010 CORRECTION COMPLETE ==========")
print("Fields corrected:", len(updates))
print("Accounting identity: PASSED")
print("Backup:", backup)
print("Dataset:", path)
print("Rows:", len(check))
print("Columns:", len(check.columns))
print("Source: NBK 2012 audited statements, PDF page 5")
print("Note: 2010 closing equity inferred from 2011 opening equity")
print("Note: Total liabilities derived from accounting identity")
print("==================================================")
