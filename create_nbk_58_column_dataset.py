import pandas as pd
from pathlib import Path

output = Path("output")
template = output / "QNB_raw_financial_data.csv"
historical_file = output / "NBK_historical_financial_indicators.csv"
destination = output / "NBK_raw_financial_data.csv"

if destination.exists():
    raise SystemExit(f"STOP: {destination} already exists.")

if not template.exists() or not historical_file.exists():
    raise SystemExit("STOP: Required source CSV is missing.")

columns = pd.read_csv(template, nrows=0).columns.tolist()

if len(columns) != 58:
    raise SystemExit("STOP: Expected exactly 58 columns.")

df = pd.DataFrame(index=range(15), columns=columns)

df["Bank_Name"] = "National Bank of Kuwait"
df["Country"] = "Kuwait"
df["Year"] = range(2010, 2025)
df["Reporting_Currency"] = "KWD"
df["Reporting_Unit"] = "Millions"

historical = pd.read_csv(historical_file)

mapping = {
    "total_assets": "Total_Assets_LCU_Millions",
    "loans_and_advances": "Loans_Advances_Islamic_Financing_LCU_Millions",
    "customer_deposits": "Customer_Accounts_Other_Deposits_LCU_Millions",
    "total_operating_income": "Total_Operating_Income_LCU_Millions",
    "profit_attributable_to_parent": "Profit_Attributable_To_Shareholders_LCU_Millions"
}

count = 0

for _, record in historical.iterrows():
    year = int(record["year"])

    if not 2010 <= year <= 2024:
        continue

    if str(record.get("currency", "")).upper() != "KWD":
        raise SystemExit(f"STOP: Unexpected currency for {year}")

    if str(record.get("unit", "")).lower() not in ("million", "millions"):
        raise SystemExit(f"STOP: Unexpected unit for {year}")

    mask = df["Year"] == year

    for source, target in mapping.items():
        if pd.notna(record.get(source)):
            value = pd.to_numeric(record[source], errors="coerce")

            if pd.notna(value):
                existing = df.loc[mask, target].iloc[0]

                if pd.notna(existing) and float(existing) != float(value):
                    raise SystemExit(
                        f"STOP: Conflicting values for {year}, {target}"
                    )

                df.loc[mask, target] = float(value)
                count += 1

    if pd.notna(record.get("source_file")):
        df.loc[mask, "Source_Document"] = record["source_file"]

    if pd.notna(record.get("source_page")):
        df.loc[mask, "Source_PDF_Page"] = record["source_page"]

df.to_csv(destination, index=False, encoding="utf-8-sig")

print("\nNBK DATASET CREATED")
print("File:", destination)
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Historical values copied:", count)
print("Years: 2010-2024")
print("Existing datasets preserved.")
