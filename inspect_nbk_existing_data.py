import pandas as pd
from pathlib import Path

print("\n========== NBK DATASET DISCOVERY ==========")

for file in sorted(Path("output").rglob("*.csv")):
    try:
        df = pd.read_csv(file, nrows=100)

        bank_columns = [
            c for c in df.columns
            if c.lower() in ("bank", "bank_name", "bank_code")
        ]

        contains_nbk = any(
            df[c].astype(str).str.contains(
                r"\bNBK\b|National Bank of Kuwait",
                case=False, regex=True, na=False
            ).any()
            for c in bank_columns
        )

        if contains_nbk or "NBK" in file.name.upper():
            print(f"\nFILE: {file}")
            print(f"COLUMNS: {len(df.columns)}")
            print(f"HEADERS: {list(df.columns)}")

            if bank_columns:
                print(df[bank_columns].head(3).to_string(index=False))

    except Exception as exc:
        print(f"Could not inspect {file}: {exc}")

print("\n========== NBK PDF INVENTORY ==========")

for file in sorted(Path("pdfs").rglob("*.pdf")):
    if "NBK" in file.name.upper() or "KUWAIT" in file.name.upper():
        print(file)

print("\nDISCOVERY COMPLETE")
