from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd

dataset = Path("output/NBK_raw_financial_data.csv")
plan = Path("output/NBK_2010_reconciliation.csv")
backup_dir = Path("output/backups")
backup_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(dataset, low_memory=False)
changes = pd.read_csv(plan)

if len(df) != 15 or len(df.columns) != 58:
    raise SystemExit("STOP: Unexpected dataset dimensions.")

if df["Year"].duplicated().any():
    raise SystemExit("STOP: Duplicate years detected.")

mask = df["Year"] == 2010

if mask.sum() != 1:
    raise SystemExit("STOP: Expected exactly one 2010 row.")

if len(changes) != 9:
    raise SystemExit("STOP: Expected nine reconciliation records.")

if changes["Field"].duplicated().any():
    raise SystemExit("STOP: Duplicate fields in reconciliation.")

if not (changes["Year"] == 2010).all():
    raise SystemExit("STOP: Unexpected year in reconciliation.")

if not (changes["Status"] == "FILL_MISSING").all():
    raise SystemExit("STOP: Reconciliation contains non-fill actions.")

for _, change in changes.iterrows():
    field = change["Field"]

    if field not in df.columns:
        raise SystemExit(f"STOP: Unknown field: {field}")

    if pd.notna(df.loc[mask, field].iloc[0]):
        raise SystemExit(f"STOP: Field already populated: {field}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = backup_dir / f"NBK_before_2010_fill_{timestamp}.csv"

shutil.copy2(dataset, backup)

for _, change in changes.iterrows():
    df.loc[mask, change["Field"]] = float(
        change["Proposed_Value"]
    )

df.to_csv(dataset, index=False)

check = pd.read_csv(dataset, low_memory=False)

if len(check) != 15 or len(check.columns) != 58:
    raise SystemExit("STOP: Dataset dimensions changed.")

for _, change in changes.iterrows():
    actual = float(
        check.loc[check["Year"] == 2010, change["Field"]].iloc[0]
    )

    expected = float(change["Proposed_Value"])

    if abs(actual - expected) > 0.000001:
        raise SystemExit(f"STOP: Verification failed: {change['Field']}")

print("\n========== NBK 2010 UPDATE COMPLETE ==========")
print("Fields populated:", len(changes))
print("Backup:", backup)
print("Dataset:", dataset)
print("Rows:", len(check))
print("Columns:", len(check.columns))
print("Existing values: PRESERVED")
print("Reconciliation report: PRESERVED")
print("================================================")
