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
    2015: (100, 102),
    2016: (103, 105),
    2017: (124, 126),
    2018: (126, 128),
}

INCOME_FIELDS = {
    "Net_Profit_LCU_Millions": ["Profit for the year"],
    "Profit_Attributable_To_Shareholders_LCU_Millions":
        ["Shareholders of the Bank"],
    "Total_Operating_Income_LCU_Millions":
        ["Net operating income"],
    "Operating_Expenses_LCU_Millions":
        ["Operating expenses"],
    "Net_Interest_Income_LCU_Millions":
        ["Net interest income and net income from"],
    "Net_Impairment_Charge_LCU_Millions": [
        "Provision charge for credit losses and impairment",
        "Provision for credit losses and impairment losses",
    ],
}

POSITION_FIELDS = {
    "Total_Assets_LCU_Millions": ["Total assets"],
    "Total_Liabilities_LCU_Millions": ["Total liabilities"],
    "Total_Equity_LCU_Millions": ["Total equity"],
    "Shareholders_Equity_LCU_Millions":
        ["Equity attributable to shareholders of the Bank"],
    "Loans_Advances_Islamic_Financing_LCU_Millions":
        ["Loans, advances and Islamic financing to"],
    "Customer_Accounts_Other_Deposits_LCU_Millions":
        ["Customer deposits"],
}

NUMBER = re.compile(
    r"(?<![\w])(?:\d{1,3}(?:,\d{3})+|\d{3,})(?![\w])"
)

def extract_value(text, labels, year, field):
    lines = [" ".join(line.split()) for line in text.splitlines()]
    candidates = []

    for index, line in enumerate(lines):
        for label in labels:
            if not line.lower().startswith(label.lower()):
                continue

            # Prevent shorter labels from matching unrelated totals.
            if label.lower() == "total liabilities":
                if line.lower().startswith("total liabilities and equity"):
                    continue

            # Look for the monetary columns on this line
            # or within the next three lines.
            window = [line[len(label):].strip()]
            window.extend(lines[index + 1:index + 4])

            for part in window:
                numbers = NUMBER.findall(part)

                if len(numbers) >= 4:
                    candidates.append(
                        int(numbers[0].replace(",", "")) / 1000
                    )
                    break

            break

    unique = sorted(set(candidates))

    if len(unique) != 1:
        raise ValueError(
            f"{year} {field}: expected one value, "
            f"found {len(unique)}; candidates={unique}"
        )

    return unique[0]

if not DATASET.exists():
    raise SystemExit(f"STOP: Dataset not found: {DATASET}")

df = pd.read_csv(DATASET)

if len(df) != 15 or len(df.columns) != 58:
    raise SystemExit("STOP: Unexpected dataset structure.")

for column in [
    "Bank_Name", "Country", "Reporting_Currency",
    "Reporting_Unit", "Source_Document",
    "Source_PDF_Page", "Source_Printed_Pages",
    "Entity_Basis_Note"
]:
    df[column] = df[column].astype("string")

results = {}

print("\n========== NBK BATCH 3 VALIDATION ==========")

for year, (income_page, position_page) in PAGES.items():
    path = PDF_DIR / f"NBK_{year}_Annual_Report.pdf"

    if not path.exists():
        raise SystemExit(f"STOP: Missing PDF: {path}")

    with pdfplumber.open(path) as pdf:
        income = pdf.pages[income_page - 1].extract_text() or ""
        position = pdf.pages[position_page - 1].extract_text() or ""

    for name, text in [
        ("income", income),
        ("financial position", position)
    ]:
        if f"31 december {year}" not in text.lower():
            raise SystemExit(
                f"STOP: Incorrect {name} statement year: {year}"
            )

        if "KD 000" not in text:
            raise SystemExit(
                f"STOP: KD thousands not confirmed: {year}"
            )

    values = {}

    for field, labels in INCOME_FIELDS.items():
        values[field] = extract_value(income, labels, year, field)

    for field, labels in POSITION_FIELDS.items():
        values[field] = extract_value(position, labels, year, field)

    assets = values["Total_Assets_LCU_Millions"]
    liabilities = values["Total_Liabilities_LCU_Millions"]
    equity = values["Total_Equity_LCU_Millions"]

    if abs(assets - liabilities - equity) > 0.001:
        raise SystemExit(
            f"STOP: Accounting identity failed for {year}: "
            f"{assets} != {liabilities} + {equity}"
        )

    mask = df["Year"] == year

    if mask.sum() != 1:
        raise SystemExit(f"STOP: Unexpected year rows: {year}")

    for field, value in values.items():
        existing = df.loc[mask, field].iloc[0]

        if pd.notna(existing):
            if abs(float(existing) - value) > 0.000001:
                raise SystemExit(
                    f"STOP: Existing value conflict for {year}, "
                    f"{field}: existing={existing}, extracted={value}"
                )

    results[year] = values

    print(
        f"VERIFIED {year}: "
        f"{len(values)} indicators, "
        f"assets={assets:,.3f}, "
        f"profit={values['Net_Profit_LCU_Millions']:,.3f}"
    )

# Only save after all four reports pass validation.
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup = BACKUP_DIR / f"NBK_before_batch3_{timestamp}.csv"
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
    df.loc[mask, "Reporting_Currency"] = "KWD"
    df.loc[mask, "Reporting_Unit"] = "Millions"
    df.loc[mask, "Entity_Basis_Note"] = (
        "NBK Group consolidated financial statements; "
        "current-year KD thousands converted to KWD millions; "
        "net interest income includes net Islamic financing income."
    )

df.to_csv(DATASET, index=False, encoding="utf-8-sig")

print("\n========== NBK BATCH 3 COMPLETE ==========")
print("Dataset:", DATASET)
print("Backup:", backup)
print("Years updated:", sorted(results))
print("Financial values processed:", sum(len(x) for x in results.values()))
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Accounting identities: PASSED")
print("Other bank datasets: UNCHANGED")
print("==========================================")
