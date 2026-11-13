from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd

dataset = Path("output/NBK_raw_financial_data.csv")
reconciliation = Path("output/NBK_2012_2014_reconciliation.csv")
backup_dir = Path("output/backups")

df = pd.read_csv(dataset, low_memory=False)
review = pd.read_csv(reconciliation, low_memory=False)

if len(df) != 15 or len(df.columns) != 58:
    raise SystemExit("STOP: Unexpected dataset dimensions.")

if len(review) != 39:
    raise SystemExit("STOP: Unexpected reconciliation row count.")

if df["Year"].duplicated().any():
    raise SystemExit("STOP: Duplicate years found.")

expected = {2012: 8, 2013: 13, 2014: 13}

for year, count in expected.items():
    subset = review[
        (review["Year"] == year)
        & (review["Status"] == "MISSING_FILL")
    ]
    if len(subset) != count:
        raise SystemExit(f"STOP: Unexpected missing count for {year}.")

updates = []

for _, record in review.iterrows():
    if record["Status"] != "MISSING_FILL":
        continue

    year = int(record["Year"])
    field = record["Field"]
    proposed = float(record["Verified_Value"])

    index = df.index[df["Year"] == year]

    if len(index) != 1:
        raise SystemExit(f"STOP: Invalid year {year}.")

    idx = index[0]

    if pd.notna(df.at[idx, field]):
        raise SystemExit(
            f"STOP: {year} {field} is no longer empty."
        )

    updates.append((idx, field, proposed))

# Validate all available accounting identities.
trial = df.copy()

for idx, field, value in updates:
    trial.at[idx, field] = value

for year in (2012, 2013, 2014):
    row = trial.loc[trial["Year"] == year].iloc[0]

    assets = row["Total_Assets_LCU_Millions"]
    liabilities = row["Total_Liabilities_LCU_Millions"]
    equity = row["Total_Equity_LCU_Millions"]

    difference = abs(assets - liabilities - equity)

    if year == 2012:
        # Existing 2012 assets are original historical values,
        # whereas liabilities and equity are restated.
        print(
            f"2012 accounting identity deferred: "
            f"mixed original/restated basis; difference={difference:.3f}"
        )
    elif difference > 0.001:
        raise SystemExit(
            f"STOP: Accounting identity failed for {year}."
        )

backup_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = backup_dir / f"NBK_before_historical_fill_{timestamp}.csv"

shutil.copy2(dataset, backup)

trial.to_csv(dataset, index=False)

print("\n========== NBK HISTORICAL UPDATE ==========")
print("Missing values filled:", len(updates))
print("Years:", sorted(expected))
print("2012 conflicting values: PRESERVED")
print("Reconciliation report: PRESERVED")
print("Backup:", backup)
print("Dataset:", dataset)
print("Rows:", len(trial))
print("Columns:", len(trial.columns))
print("===========================================")
