import re
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd
import pdfplumber

DATASET = Path("output/NBK_raw_financial_data.csv")
PDF_DIR = Path("pdfs/NBK")
BACKUP_DIR = Path("output/backups")

PAGES = {
    2019: (108, 110),
    2020: (111, 113),
    2021: (117, 119),
    2022: (117, 119),
}

INCOME_FIELDS = {
    "Net_Profit_LCU_Millions": "Profit for the year",
    "Profit_Attributable_To_Shareholders_LCU_Millions": "Shareholders of the Bank",
    "Total_Operating_Income_LCU_Millions": "Net operating income",
    "Operating_Expenses_LCU_Millions": "Operating expenses",
    "Net_Interest_Income_LCU_Millions":
        "Net interest income and net income from Islamic financing",
    "Net_Impairment_Charge_LCU_Millions":
        "Provision charge for credit losses and impairment losses",
}

POSITION_FIELDS = {
    "Total_Assets_LCU_Millions": "Total assets",
    "Total_Liabilities_LCU_Millions": "Total liabilities",
    "Total_Equity_LCU_Millions": "Total equity",
    "Shareholders_Equity_LCU_Millions":
        "Equity attributable to shareholders of the Bank",
    "Loans_Advances_Islamic_Financing_LCU_Millions":
        "Loans, advances and Islamic financing to customers",
    "Customer_Accounts_Other_Deposits_LCU_Millions":
        "Customer deposits",
}

def extract_value(text, label):
    matches = []

    for line in text.splitlines():
        line = " ".join(line.split())

        if not line.lower().startswith(label.lower() + " "):
            continue

        remainder = line[len(label):].strip()

        # Remove an optional financial-statement note number.
        tokens = remainder.split()
        if len(tokens) >= 5 and re.fullmatch(r"\d{1,2}", tokens[0]):
            tokens = tokens[1:]

        if len(tokens) < 4:
            continue

        # The first two values are current and comparative KD 000s.
        if not all(re.fullmatch(r"[\d,]+", x) for x in tokens[:2]):
            continue

        matches.append(int(tokens[0].replace(",", "")) / 1000)

    if len(matches) != 1:
        raise ValueError(
            f"Expected one match for '{label}', found {len(matches)}"
        )

    return matches[0]

if not DATASET.exists():
    raise SystemExit(f"STOP: Missing dataset: {DATASET}")

df = pd.read_csv(DATASET)

if len(df.columns) != 58 or len(df) != 15:
    raise SystemExit("STOP: Unexpected NBK dataset structure.")

text_columns = [
    "Bank_Name", "Country", "Reporting_Currency",
    "Reporting_Unit", "Source_Document",
    "Source_PDF_Page", "Source_Printed_Pages",
    "Entity_Basis_Note"
]

for column in text_columns:
    df[column] = df[column].astype("string")

results = {}

# Extract and validate all four reports before modifying the CSV.
for year, (income_page, position_page) in PAGES.items():
    path = PDF_DIR / f"NBK_{year}_Annual_Report.pdf"

    if not path.exists():
        raise SystemExit(f"STOP: Missing PDF: {path}")

    with pdfplumber.open(path) as pdf:
        income = pdf.pages[income_page - 1].extract_text() or ""
        position = pdf.pages[position_page - 1].extract_text() or ""

    if f"31 December {year}" not in income:
        raise SystemExit(f"STOP: Income statement year mismatch: {year}")

    if f"31 December {year}" not in position:
        raise SystemExit(f"STOP: Financial position year mismatch: {year}")

    if "KD 000" not in income or "KD 000" not in position:
        raise SystemExit(f"STOP: Currency units not confirmed: {year}")

    values = {}

    for field, label in INCOME_FIELDS.items():
        values[field] = extract_value(income, label)

    for field, label in POSITION_FIELDS.items():
        values[field] = extract_value(position, label)

    assets = values["Total_Assets_LCU_Millions"]
    liabilities = values["Total_Liabilities_LCU_Millions"]
    equity = values["Total_Equity_LCU_Millions"]

    if abs(assets - liabilities - equity) > 0.001:
        raise SystemExit(f"STOP: Accounting identity failed: {year}")

    mask = df["Year"] == year

    if mask.sum() != 1:
        raise SystemExit(f"STOP: Unexpected dataset rows: {year}")

    for field, value in values.items():
        existing = df.loc[mask, field].iloc[0]

        if pd.notna(existing) and abs(float(existing) - value) > 0.000001:
            raise SystemExit(
                f"STOP: Conflicting value: {year}, {field}. "
                f"Existing={existing}, extracted={value}"
            )

    results[year] = values

    print(
        f"VERIFIED {year}: "
        f"{len(values)} indicators, "
        f"assets={assets:,.3f}, "
        f"profit={values['Net_Profit_LCU_Millions']:,.3f}"
    )

# Create backup only after every year has passed validation.
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = BACKUP_DIR / f"NBK_before_batch2_{timestamp}.csv"
shutil.copy2(DATASET, backup)

for year, values in results.items():
    mask = df["Year"] == year
    income_page, position_page = PAGES[year]

    for field, value in values.items():
        df.loc[mask, field] = value

    df.loc[mask, "Source_Document"] = (
        f"NBK_{year}_Annual_Report.pdf"
    )
    df.loc[mask, "Source_PDF_Page"] = (
        f"{income_page};{position_page}"
    )
    df.loc[mask, "Source_Printed_Pages"] = (
        f"{income_page - 4};{position_page - 4}"
    )
    df.loc[mask, "Reporting_Currency"] = "KWD"
    df.loc[mask, "Reporting_Unit"] = "Millions"
    df.loc[mask, "Entity_Basis_Note"] = (
        "NBK Group consolidated statements; "
        "current-year KD thousands converted to KWD millions; "
        "net interest income includes net Islamic financing income."
    )

df.to_csv(DATASET, index=False, encoding="utf-8-sig")

print("\n========== NBK BATCH 2 COMPLETE ==========")
print("Dataset:", DATASET)
print("Backup:", backup)
print("Years updated:", sorted(results))
print("Indicators processed:", sum(map(len, results.values())))
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Accounting identities: PASSED")
print("Other bank datasets: UNCHANGED")
print("==========================================")
