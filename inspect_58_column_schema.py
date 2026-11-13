import pandas as pd
from pathlib import Path

print("\n========== EXISTING 58-COLUMN DATASETS ==========")

found = 0

for file in sorted(Path("output").rglob("*.csv")):
    try:
        df = pd.read_csv(file, nrows=0)

        if len(df.columns) == 58:
            found += 1
            print(f"\nFILE: {file}")
            print("COLUMNS:", len(df.columns))

            for i, column in enumerate(df.columns, 1):
                print(f"{i:02d}. {column}")

    except Exception as exc:
        print(f"ERROR reading {file}: {exc}")

print("\nTOTAL 58-COLUMN DATASETS:", found)
