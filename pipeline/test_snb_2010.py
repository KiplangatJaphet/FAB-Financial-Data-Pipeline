import csv
import re
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]

PDF_PATH = ROOT / "pdfs/SNB/NCB_2010_Annual_Report.pdf"
SCHEMA_PATH = ROOT / "output/SNB_raw_financial_data.csv"


def parse_amount(value):
    value = value.strip().replace(",", "")

    if value == "-":
        return 0.0

    negative = value.startswith("(") and value.endswith(")")
    value = value.strip("()")

    number = float(value) / 1000

    return -number if negative else number


def extract_value(text, label):
    amount = r"\(?[\d,]+\)?"

    pattern = (
        rf"^{re.escape(label)}"
        rf"(?:\s+[\d.&]+)?"
        rf"\s+({amount})\s+({amount})\s*$"
    )

    matches = []

    for line in text.splitlines():
        match = re.match(pattern, line.strip(), re.I)

        if match:
            matches.append(parse_amount(match.group(1)))

    if not matches:
        raise ValueError(f"Missing financial field: {label}")

    if len(set(matches)) != 1:
        raise ValueError(f"Conflicting values: {label}")

    return matches[0]


def main():
    with SCHEMA_PATH.open(
        encoding="utf-8-sig", newline=""
    ) as f:
        columns = next(csv.reader(f))

    if len(columns) != 58:
        raise ValueError("Expected exactly 58 columns.")

    record = dict.fromkeys(columns, "")

    with pdfplumber.open(PDF_PATH) as pdf:
        balance = pdf.pages[35].extract_text() or ""
        income = pdf.pages[36].extract_text() or ""

    record.update({
        "Bank_Name": "Saudi National Bank",
        "Country": "Saudi Arabia",
        "Year": 2010,

        "Total_Assets_LCU_Millions":
            extract_value(balance, "Total assets"),

        "Total_Liabilities_LCU_Millions":
            extract_value(balance, "Total liabilities"),

        "Total_Equity_LCU_Millions":
            extract_value(balance, "Total shareholders’ equity"),

        "Shareholders_Equity_LCU_Millions":
            extract_value(
                balance,
                "Total shareholders’ equity attributable to equity holders of the Parent"
            ),

        "Net_Profit_LCU_Millions":
            extract_value(income, "Net income for the year"),

        "Total_Operating_Income_LCU_Millions":
            extract_value(income, "Operating income"),

        "Operating_Expenses_LCU_Millions":
            extract_value(income, "Operating expenses"),

        "Net_Interest_Income_LCU_Millions":
            extract_value(income, "Net special commission income"),

        "Loans_Advances_Islamic_Financing_LCU_Millions":
            extract_value(balance, "Loans and advances, net"),

        "Customer_Accounts_Other_Deposits_LCU_Millions":
            extract_value(balance, "Customers’ deposits"),

        "Reporting_Currency": "SAR",
        "Reporting_Unit": "Millions",
        "Source_Document": PDF_PATH.name,
        "Source_PDF_Page": "36;37",
        "Source_Printed_Pages": "34;35",
        "Entity_Basis_Note":
            "NCB consolidated financial statements; predecessor of SNB",
    })

    assets = record["Total_Assets_LCU_Millions"]
    liabilities = record["Total_Liabilities_LCU_Millions"]
    equity = record["Total_Equity_LCU_Millions"]

    if abs(assets - liabilities - equity) > 0.001:
        raise ValueError("Balance sheet reconciliation failed.")

    print("\nSNB 2010 EXTRACTION TEST")
    print("=" * 55)

    populated = 0

    for column, value in record.items():
        if value != "":
            populated += 1
            print(f"{column}: {value}")

    print("\nTotal columns:", len(record))
    print("Populated columns:", populated)
    print("Unpopulated columns:", len(record) - populated)
    print("Balance sheet reconciliation: PASS")
    print("Existing datasets: UNCHANGED")


if __name__ == "__main__":
    main()
