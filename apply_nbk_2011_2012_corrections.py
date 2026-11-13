from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd

dataset = Path("output/NBK_raw_financial_data.csv")
plan = Path("output/NBK_2011_2012_correction_plan.csv")
backup_dir = Path("output/backups")

df = pd.read_csv(dataset, low_memory=False)
review = pd.read_csv(plan, low_memory=False)

if len(df) != 15 or len(df.columns) != 58:
    raise SystemExit("STOP: Unexpected dataset dimensions.")

if len(review) != 26:
    raise SystemExit("STOP: Unexpected correction plan size.")

if df["Year"].duplicated().any():
    raise SystemExit("STOP: Duplicate years detected.")

expected = {
    (2011, "FILL_MISSING"): 8,
    (2011, "REPLACE_REVIEW"): 5,
    (2012, "REPLACE_REVIEW"): 5,
    (2012, "UNCHANGED"): 8,
}

actual = review.groupby(["Year", "Status"]).size().to_dict()

if actual != expected:
    raise SystemExit(
        f"STOP: Correction plan counts changed: {actual}"
    )

trial = df.copy()
changes = []

for _, record in review.iterrows():
    year = int(record["Year"])
    field = record["Field"]
    status = record["Status"]
    proposed = float(record["Proposed_Value"])

    matching = trial.index[trial["Year"] == year]

    if len(matching) != 1:
        raise SystemExit(f"STOP: Invalid year {year}.")

    idx = matching[0]
    current = pd.to_numeric(
        pd.Series([df.at[idx, field]]),
        errors="coerce"
    ).iloc[0]

    planned_existing = record["Existing_Value"]

    if pd.isna(planned_existing):
        if pd.notna(current):
            raise SystemExit(
                f"STOP: {year} {field} is no longer empty."
            )
    elif pd.isna(current) or abs(
        float(current) - float(planned_existing)
    ) > 0.000001:
        raise SystemExit(
            f"STOP: Existing value changed: {year} {field}"
        )

    if status == "UNCHANGED":
        if pd.isna(current) or abs(
            float(current) - proposed
        ) >= 0.001:
            raise SystemExit(
                f"STOP: Unexpected unchanged value: {year} {field}"
            )
        continue

    if status not in ("FILL_MISSING", "REPLACE_REVIEW"):
        raise SystemExit(f"STOP: Unknown status {status}")

    trial.at[idx, field] = proposed
    changes.append((year, field, status))

# Verify accounting identities before saving.
for year in (2011, 2012):
    row = trial.loc[trial["Year"] == year].iloc[0]

    assets = row["Total_Assets_LCU_Millions"]
    liabilities = row["Total_Liabilities_LCU_Millions"]
    equity = row["Total_Equity_LCU_Millions"]

    difference = abs(assets - liabilities - equity)

    if difference > 0.001:
        raise SystemExit(
            f"STOP: Accounting identity failed for {year}: "
            f"difference={difference:.6f}"
        )

# Backup before writing.
backup_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = backup_dir / f"NBK_before_2011_2012_correction_{timestamp}.csv"

if backup.exists():
    raise SystemExit("STOP: Backup filename already exists.")

shutil.copy2(dataset, backup)

# Save the validated dataset.
trial.to_csv(dataset, index=False)

print("\n========== NBK CORRECTION COMPLETE ==========")
print("Changes applied:", len(changes))
print("Missing values filled:", sum(
    status == "FILL_MISSING"
    for _, _, status in changes
))
print("Existing values corrected:", sum(
    status == "REPLACE_REVIEW"
    for _, _, status in changes
))
print("2011 accounting identity: PASSED")
print("2012 accounting identity: PASSED")
print("Original values retained in:", plan)
print("Backup:", backup)
print("Dataset:", dataset)
print("Rows:", len(trial))
print("Columns:", len(trial.columns))
print("=============================================")
